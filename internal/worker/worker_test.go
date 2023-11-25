package worker

import (
	"fmt"
	"os/exec"
	"testing"
)

var baseURL = "http://0.0.0.0:8000"

func TestGetSpecs(t *testing.T) {
	specs, err := GetMachineSpecs()
	if err != nil {
		t.Errorf("Error getting machine specs: %s", err)
	} else {
		t.Logf("Got machine specs: %+v", specs)
	}
}

// func TestInitWorker(t *testing.T) (*WorkerImpl, error) {
// 	client := InitRestClient(baseURL)
// 	worker, err := InitWorker(client)
// 	if err != nil {
// 		t.Errorf("Error initializing worker: %s", err)
// 	} else {
// 		t.Logf("Initialized worker: %+v", worker)
// 	}
// 	return worker, err
// }

func TestRegisterWorker(t *testing.T) {
	worker, err := InitWorker(InitRestClient(baseURL))
	if err != nil {
		t.Errorf("Error registering worker: %s", err)
	} else {
		workerId, err := worker.RegisterWorker()
		if err != nil {
			t.Errorf("Error registering worker: %s", err)
		} else {
			t.Logf("Registered worker with ID: %d", &workerId)
		}
	}

}

func TestGetWork(t *testing.T) {
	client := InitRestClient(baseURL)
	worker, err := InitWorker(client)
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
		if err != nil {
			t.Errorf("Error registering worker: %s", err)
		} else {
			t.Logf("Registered worker with ID: %d", &workerId)
			work, err := worker.GetWork()
			if err != nil {
				t.Errorf("Error getting work: %s", err)
			} else {
				t.Logf("Got work: %+v", work)
			}
		}
	}
}

func TestSubmitWork(t *testing.T) {
	client := InitRestClient(baseURL)
	worker, err := InitWorker(client)
	if err != nil {
		t.Errorf("Error init worker: %s", err)
	}
	workerId, err := worker.RegisterWorker()
	if err != nil {
		t.Errorf("Error registering worker: %s", err)
	} else {
		t.Logf("Registered worker with ID: %d", &workerId)
		if err != nil {
			t.Errorf("Error getting work: %s", err)
		} else {
			t.Logf("Got work:")
		}
	}
}

func TestExecuteWork(t *testing.T) {
	client := InitRestClient(baseURL)
	worker, err := InitWorker(client)
	WorkPackage := CreateWorkPackage()
	if err != nil {
		t.Errorf("Error init worker work: %s", err)
	}
	res, err := worker.ExecuteWork(&WorkPackage)
	fmt.Printf("res: %+v", res)
	if err != nil {
		t.Errorf("Error executing work: %s", err)
	} else {
		t.Logf("Executed work: %+v", res)
	}
}

func CreateWorkPackage() WorkPackage {

	id := "ce670188-5567-4b51-a8c5-d894dbfbacbd"

	WorkPackage := WorkPackage{
		ID: &id,
		Queries: []QueryTargetType{
			{
				Query:  "0e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
				Target: "2e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
			},
			{
				Query:  "1e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
				Target: "3e22cdce-68b5-4f94-a8a0-2980cbeeb74c",
			}},
		Sequences: map[SequenceId]Sequence{
			"0e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ADG",
			"1e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ATGATCGATCGATCG",
			"2e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
			"3e22cdce-68b5-4f94-a8a0-2980cbeeb74c": "ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
		},
	}
	return WorkPackage
}

func CreateJob() string {
	cmd := exec.Command("bash", "-c", "./create_master_curl.sh")
	stdoutStderr, err := cmd.CombinedOutput() // This will capture both stdout and stderr
	if err != nil {
		fmt.Printf("Error: %s\n", err)
	}
	fmt.Printf("%s\n", stdoutStderr)
	return string(stdoutStderr)
}
