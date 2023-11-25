package worker

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type Sequence string
type SequenceId string

type QueryTargetType struct {
	Query  SequenceId `json:"query"`
	Target SequenceId `json:"target"`
}

type Alignment struct {
	AlignmentString string `json:"alignment"`
	Length          int    `json:"length"`
	Score           int    `json:"score"`
}

type WorkPackage struct {
	ID        *string                 `json:"id"`
	Queries   []QueryTargetType       `json:"queries"`
	Sequences map[SequenceId]Sequence `json:"sequences"`
}

type MachineSpecsRequest struct {
	//For now only cpu resources

	// Cores       uint `json:"cores"`
	// Cpus        uint `json:"cpus"`
	// Threads     uint `json:"threads"`
	// MemorySpeed uint `json:"memory_speed"`
	// MemorySize  uint `json:"memory_size"`
	// GPU         bool `json:"gpu_resources"`

	Ram uint `json:"ram_mb"`
	Cpu uint `json:"cpu_resources"`
	Gpu uint `json:"gpu_resources"`
}

type WorkRequest struct {
	WorkerId string `json:"id"`
}
type Heartbeat struct {
	WorkerId string `json:"id"`
}

type TargetQueryCombination struct {
	Target SequenceId `json:"target"`
	Query  SequenceId `json:"query"`
}

type WorkResult struct {
	Alignments []AlignmentDetail `json:"alignments"`
}

type AlignmentDetail struct {
	TargetQueryCombination TargetQueryCombination `json:"combination"`
	Alignment              Alignment              `json:"alignment"`
}

type RestClient struct {
	baseURL string
	client  *http.Client
}

func InitRestClient(baseURL string) *RestClient {
	return &RestClient{
		baseURL: baseURL,
		client:  &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *RestClient) RegisterWorker(specs *MachineSpecs) (*string, error) {
	//TODO: Machine specs vaildation
	specsReq := MachineSpecsRequest{
		Ram: 800,
		Cpu: 1,
		Gpu: specs.gpu,
	}
	jsonData, err := json.Marshal(specsReq)
	fmt.Println("Registering worker")
	fmt.Println(string(jsonData))
	req, err := http.NewRequest("POST", c.baseURL+"/worker/register", bytes.NewBuffer(jsonData))
	if err != nil {
		fmt.Println("Error creating request", err)
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, err
	}

	defer resp.Body.Close()

	var workReq WorkRequest
	if err := json.NewDecoder(resp.Body).Decode(&workReq); err != nil {
		fmt.Println("Error decoding response", err)
		return nil, err
	}
	fmt.Println("Registered worker")
	fmt.Println(workReq)
	//TODO: Maybe we should return the workReq
	return &workReq.WorkerId, nil
}

func (c *RestClient) RequestWork(workerId string) (*WorkPackage, error) {
	fmt.Println("Requesting work")
	workReq := WorkRequest{WorkerId: workerId}
	jsonData, err := json.Marshal(workReq)

	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", c.baseURL+"/work", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	fmt.Printf("Requesting work from %s\n", c.baseURL+"/work")

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		fmt.Println("Error sending request", err)
		return nil, err
	}

	//Assuming the response has a body
	defer resp.Body.Close()

	// Did not get a 200 OK response
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status: %s", resp.Status)
	}

	// Read the response
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	// Decode the response
	var workPkg WorkPackage
	err = json.Unmarshal(body, &workPkg)
	if err != nil {
		fmt.Printf("Error decoding response: %s", err)
		return nil, err
	}
	fmt.Println("Got work", &workPkg)
	return &workPkg, nil
}

func (c *RestClient) SendResult(result WorkResult, workId string) error {
	jsonData, err := json.Marshal(result)
	if err != nil {
		return err
	}

	req, err := http.NewRequest("POST", c.baseURL+"/work/"+workId+"/result", bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")

	fmt.Println("Sending result to url: " + c.baseURL + "/work/" + workId + "/result")
	fmt.Println(string(jsonData))

	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}

	//Assuming the response has a body
	defer resp.Body.Close()

	// Did not get a 200 OK response
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status: %s", resp.Status)
	}

	return nil
}

func (c *RestClient) SendHeartbeat(workerId string) error {
	heartbeat := Heartbeat{WorkerId: workerId}
	jsonData, err := json.Marshal(heartbeat)
	if err != nil {
		return err
	}
	fmt.Println("Sending heartbeat to url: " + c.baseURL + "/worker/pulse")
	fmt.Println(string(jsonData))
	resp, err := c.client.Post(c.baseURL+"/worker/pulse", "application/json", bytes.NewReader(jsonData))
	resp.Body.Close()
	return err
}
