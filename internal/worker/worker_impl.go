package worker

import (
	"dlsa/internal/smithwaterman"
	"errors"
	"fmt"
	"log"
	"runtime"
	"sync"
	"time"
)

// Implementation of the worker interface
// the worker has a worker ID, which can be null
// The worker also has a work package, which contains the queries and targets
// The worker also contains its benchmark result

type Worker struct {
	specs    *MachineSpecs // Machine specs of the worker
	workerId *string       // Unique ID of the worker
	client   *RestClient   // Client to communicate with the master
	status   Status
}

type Status byte

const (
	Waiting Status = 0
	Working Status = 1
	Dead    Status = 2
)

const heartbeatIntervalInSeconds = 8

func InitWorker(client *RestClient, benchmark float32) *Worker {
	machineSpecs := GetMachineSpecs(benchmark)
	return &Worker{
		specs:  machineSpecs,
		client: client,
		status: Waiting,
	}
}

// RegisterWorker Function to register the worker with the master, returns the worker ID if successful
// TODO: Decide what happens if the worker is already registered ()
func (w *Worker) RegisterWorker() (*string, error) {
	// Logic to register the worker, call the register endpoint
	workerId, err := w.client.RegisterWorker(w.specs)
	if err != nil {
		return nil, err
	}
	w.workerId = workerId
	go w.heartbeatRoutine()
	return workerId, nil
}

// GetWork Function to request work from the master, returns the work package if successful
func (w *Worker) GetWork() (*CompleteWorkPackage, error) {
	work, err := w.client.RequestWork(*w.workerId)
	if err != nil {
		return nil, err
	}
	if work == nil {
		return nil, nil
	}

	return w.GetSequencesForWork(work)
}

func (w *Worker) GetSequencesForWork(workPackage *WorkPackage) (*CompleteWorkPackage, error) {

	// Create a map of sequence IDs to sequences
	sequences := make(map[SequenceId]Sequence)

	var addIfNotPresent = func(id SequenceId) error {
		_, ok := sequences[id]
		if !ok {
			sequence, err := w.client.RequestSequence(*workPackage.ID, id, w.workerId)
			if err != nil {
				return err
			}
			sequences[id] = *sequence
		}
		return nil

	}

	for _, query := range workPackage.Queries {
		err := addIfNotPresent(query.Query)
		if err != nil {
			return nil, err
		}
		err = addIfNotPresent(query.Target)
		if err != nil {
			return nil, err
		}
	}

	// Return the work package with the sequences
	return &CompleteWorkPackage{
		WorkPackage: workPackage,
		Sequences:   sequences,
	}, nil
}

// ExecuteWork Function to execute the work package, returns the work result for every pair if successful
// For now we just execute the work sequentially and send the result back for every seq,tar pair
func (w *Worker) ExecuteWork(work *CompleteWorkPackage, queries []QueryTargetType) {
	w.status = Working

	// A list of results that are then sent batched to the master
	bufferSize := 100
	workResultBuffer := WorkResult{Alignments: make([]AlignmentDetail, 0)}

	for idx, comb := range queries {
		targetSeq, ok1 := work.Sequences[comb.Target]
		querySeq, ok2 := work.Sequences[comb.Query]

		// Check if both sequences are in the work package
		if !ok1 || !ok2 {
			log.Fatalf("Target and query not found in work package")
		}

		// qRes, _, score := smithwaterman.FindLocalAlignment(string(querySeq), string(targetSeq), work.MatchScore, work.MismatchPenalty, work.GapPenalty)

		rustRes, err := findAlignmentWithFallback(string(querySeq), string(targetSeq),
			smithwaterman.AlignmentScore{MatchScore: work.MatchScore, MismatchPenalty: -work.MismatchPenalty, GapPenalty: -work.GapPenalty})

		if err != nil {
			// TODO: What now?
			// At least we want some logging here, but we should probably
			// mention to the master that there is a problem
			log.Printf("%s\n", err)
		}

		qRes := rustRes.Query
		tRes := rustRes.Target
		score := int(rustRes.Score)
		maxX := int(rustRes.MaxX)
		maxY := int(rustRes.MaxY)

		alignment := AlignmentDetail{
			Alignment: Alignment{
				QueryAlignment:  qRes,
				TargetAlignment: tRes,
				Score:           score,
				Length:          len(qRes),
				MaxX:            maxX,
				MaxY:            maxY,
			},
			TargetQueryCombination: TargetQueryCombination{
				Query:  comb.Query,
				Target: comb.Target,
			},
		}

		// Append the alignment to the buffer
		workResultBuffer.Alignments = append(workResultBuffer.Alignments, alignment)
		// If the buffer is full, send the results
		if idx%bufferSize == 0 && idx > 0 {
			go w.client.SendResult(workResultBuffer, *work.ID)
			// Clear the buffer
			workResultBuffer = WorkResult{Alignments: make([]AlignmentDetail, 0)}
		}
	}
	w.client.SendResult(workResultBuffer, *work.ID)
	w.status = Waiting
}

func findAlignmentWithFallback(query, target string, alignmentScore smithwaterman.AlignmentScore) (*GoResult, error) {
	var rustRes *GoResult
	var err error

	rustRes, err = FindRustAlignmentSimdLowMem(query, target, alignmentScore)

	if err == nil {
		return rustRes, nil
	}

	fmt.Printf("Error in SIMD low memory alignment, falling back to smid: %s\n", err)
	fmt.Printf("Query: %s\n", query)
	fmt.Printf("Target: %s\n", target)

	rustRes, err = FindRustAlignmentSimd(query, target, alignmentScore)

	if err == nil {
		return rustRes, nil
	}

	fmt.Printf("Error in SIMD alignment, falling back to sequential: %s\n", err)
	fmt.Printf("Query: %s\n", query)
	fmt.Printf("Target: %s\n", target)

	rustRes, err = FindRustAlignmentSequential(query, target, alignmentScore)

	if err == nil {
		return rustRes, nil
	}

	return nil, errors.New("All alignment functions failed to align a sequence")

}

func (w *Worker) ExecuteWorkInParallel(work *CompleteWorkPackage) {
	var cpuCount = runtime.NumCPU() - 1
	var workPackages = work.Queries
	var numWorkPackages = len(workPackages)

	// Split the work packages into chunks
	var chunks = make([][]QueryTargetType, cpuCount)
	for i := 0; i < cpuCount; i++ {
		var start = numWorkPackages * i / cpuCount
		var end = numWorkPackages * (i + 1) / cpuCount
		chunks[i] = workPackages[start:end]
	}
	var wg sync.WaitGroup

	for i := 0; i < cpuCount; i++ {
		wg.Add(1)

		tmp := i
		go func() {
			defer wg.Done()

			w.ExecuteWork(work, chunks[tmp])
		}()
	}

	wg.Wait()
}

func (w *Worker) heartbeatRoutine() {
	for w.status != Dead {
		time.Sleep(heartbeatIntervalInSeconds * time.Second)
		w.client.SendHeartbeat(*w.workerId)
	}
}
