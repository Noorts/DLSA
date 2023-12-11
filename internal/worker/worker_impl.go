package worker

import (
	"dlsa/internal/smithwaterman"
	"log"
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
func (w *Worker) GetWork() (*WorkPackage, error) {
	return w.client.RequestWork(*w.workerId)
}

// ExecuteWork Function to execute the work package, returns the work result for every pair if successful
// For now we just execute the work sequentially and send the result back for every seq,tar pair
// TODO: This seems kinda hacky for now idk should think about this
// TODO: Parallelization work
func (w *Worker) ExecuteWork(work *WorkPackage) {
	w.status = Working

	// A list of results that are then sent batched to the master
	bufferSize := 100
	workResultBuffer := WorkResult{Alignments: make([]AlignmentDetail, 0)}

	for idx, comb := range work.Queries {
		targetSeq, ok1 := work.Sequences[comb.Target]
		querySeq, ok2 := work.Sequences[comb.Query]

		// Check if both sequences are in the work package
		if !ok1 || !ok2 {
			log.Fatalf("Target and query not found in work package")
		}

		qRes, _, score := smithwaterman.FindLocalAlignment(string(targetSeq), string(querySeq), work.MatchScore, work.MismatchPenalty, work.GapPenalty)
		// rustRes := FindRustAlignmentSimd(string(targetSeq), string(querySeq))
		// qRes := rustRes.Query
		// score := rustRes.Score

		alignment := AlignmentDetail{
			Alignment: Alignment{
				AlignmentString: qRes,
				Score:           score,
				Length:          len(qRes),
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

func (w *Worker) heartbeatRoutine() {
	for w.status != Dead {
		time.Sleep(heartbeatIntervalInSeconds * time.Second)
		w.client.SendHeartbeat(*w.workerId)
	}
}
