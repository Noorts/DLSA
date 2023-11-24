package worker

import (
	"dlsa/internal/smithwaterman"
	"log"
	"time"
)

// Implementation of the worker interface
// the worker has a worker ID, which can be null
// The worker also has a work package, which contains the queries and targets
// The worker also contains it's specs (CPU, RAM, etc.)

type WorkerImpl struct {
	specs    *MachineSpecs // Machine specs of the worker
	workerId *string       // Unique ID of the worker
	// workPackage *WorkPackage  // Work package of the worker, can be null
	client *RestClient // Client to communicate with the master
	status Status
}

type Status byte

const (
	Waiting Status = 0
	Working Status = 1
	Dead    Status = 2
)

// TODO: Decide what happens if the specs arent't returned return nil for now
func InitWorker(client *RestClient) (*WorkerImpl, error) {
	machineSpecs, err := GetMachineSpecs()
	if err != nil {
		return nil, err
	}
	return &WorkerImpl{
		specs:  machineSpecs,
		client: client,
		status: Waiting,
	}, nil
}

// Function to register the worker with the master, returns the worker ID if successful
// TODO: Decide what happens if the worker is already registered ()
func (w *WorkerImpl) RegisterWorker() (*string, error) {
	// Logic to register the worker, call the register endpoint
	workerId, err := w.client.RegisterWorker(w.specs)
	if err != nil {
		return nil, err
	}
	w.workerId = workerId
	go w.heartbeatRoutine()
	return workerId, nil
}

// Function to request work from the master, returns the work package if successful
func (w *WorkerImpl) GetWork() (*WorkPackage, error) {
	// Logic to fetch a task from the master, call the work endpoint
	if w.workerId == nil {
		//some error message
	}
	work, err := w.client.RequestWork(*w.workerId)
	if err != nil {
		return nil, err
	}
	return work, nil
}

// Function to execute the work package, returns the work result for every pair if successful
// For now we just execute the work sequentially and send the result back for every seq,tar pair
// TODO: This seems kinda hacky for now idk should think about this
// TODO: Parallelization work
func (w *WorkerImpl) ExecuteWork(work *WorkPackage) ([]WorkResult, error) {
	w.status = Working
	results := make([]WorkResult, len(work.Sequences))
	for ind, comb := range work.Sequences {
		targetSeq, ok1 := work.Targets[comb.Target]
		querySeq, ok2 := work.Queries[comb.Query]

		// Check if both sequences are in the work package
		if !ok1 || !ok2 {
			log.Fatalf("Target and query not found in work package")
			continue
		}

		stringScore := smithwaterman.FindStringScore(string(targetSeq), string(querySeq))
		resultString := "ASDFADFSD" //for now since SW only returns that matrix

		alignment := AlignmentDetails{
			Alignment: Alignment{
				AlignmentString: resultString,
				Score:           10,
				Length:          len(stringScore),
			},
			Combination: TargetQueryCombination{comb.Target, comb.Query},
		}

		result := WorkResult{
			WorkID:     work.ID,
			Alignments: []AlignmentDetails{alignment},
		}

		log.Printf("Result: %v", result)
		err := w.client.SendResult(result)
		if err != nil {
			//TODO: Should we just log the error and continue?
			log.Printf("Error sending result: %v", err)
			continue
		}
		results[ind] = result
	}
	w.status = Waiting
	return results, nil
}

func (w *WorkerImpl) heartbeatRoutine() {
	for w.status != Dead {
		time.Sleep(30 * time.Second)
		for w.client.SendHeartbeat(*w.workerId) != nil {
			time.Sleep(2 * time.Second)
		}
	}
}
