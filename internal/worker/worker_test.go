package worker

import (
	"testing"
)

var baseURL = "http://localhost:8080"

func TestGetSpecs(t *testing.T) {
	specs, err := GetMachineSpecs()
	if err != nil {
		t.Errorf("Error getting machine specs: %s", err)
	} else {
		t.Logf("Got machine specs: %+v", specs)
	}
}

func InitTestWorker(t *testing.T) (*Worker, error) {
	client := InitRestClient(baseURL)
	worker, err := InitWorker(client)
	if err != nil {
		t.Errorf("Error initializing worker: %s", err)
	} else {
		t.Logf("Initialized worker: %+v", worker)
	}
	return worker, err
}

func TestRegisterWorker(t *testing.T) {
	worker, err := InitTestWorker(t)
	if err != nil {
		t.Errorf("Error registering worker: %s", err)
	} else {
		workerId, err := worker.RegisterWorker()
		if err != nil {
			t.Errorf("Error registering worker: %s", err)
		} else {
			t.Logf("Registered worker with ID: %d", *workerId)
		}
	}

}

func TestGetWork(t *testing.T) {
	worker, err := InitTestWorker(t)
	if err != nil {
		t.Errorf("Error getting work: %s", err)
	} else {
		work, err := worker.GetWork()
		//assert that we cannot get work without registering
		if err != nil {
			t.Errorf("Error getting work: %s", err)
		} else {
			t.Logf("Got work: %+v", work)
		}
		//then register and get work
		workerId, err := worker.RegisterWorker()

	}
}

func TestExecuteWork() {

}
