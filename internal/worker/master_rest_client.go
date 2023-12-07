package worker

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
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
	ID              *string                 `json:"id"`
	JobID           *string                 `json:"job_id"`
	Queries         []QueryTargetType       `json:"queries"`
	Sequences       map[SequenceId]Sequence `json:"sequences"`
	MatchScore      int                     `json:"match_score"`
	MismatchPenalty int                     `json:"mismatch_penalty"`
	GapPenalty      int                     `json:"gap_penalty"`
}

type MachineSpecsRequest struct {
	Benchmark float32 `json:"benchmark_result"`
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
	specsReq := MachineSpecsRequest{
		Benchmark: specs.benchmark,
	}
	jsonData, err := json.Marshal(specsReq)
	log.Println("Registering worker")
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
	return &workReq.WorkerId, nil
}

func (c *RestClient) RequestWork(workerId string) (*WorkPackage, error) {
	workReq := WorkRequest{WorkerId: workerId}
	jsonData, err := json.Marshal(workReq)

	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", c.baseURL+"/work/", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	resp, err := c.client.Do(req)
	if err != nil {
		log.Println("Could not retrieve work", err)
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

	// check if the body is a byte array of null
	if string(body) == "null" {
		return nil, nil
	}

	// Decode the response
	var workPkg WorkPackage
	err = json.Unmarshal(body, &workPkg)
	if err != nil {
		fmt.Printf("Error decoding response: %s", err)
		return nil, err
	}
	return &workPkg, nil
}

func (c *RestClient) SendResult(result WorkResult, workId string) {
	jsonData, err := json.Marshal(result)
	if err != nil {
		log.Println("Error marshalling result", err)
		return
	}

	req, err := http.NewRequest("POST", c.baseURL+"/work/"+workId+"/result", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Println("Error creating request", err)
		return
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		log.Println("Error sending result", err)
		return
	}

	//Assuming the response has a body
	defer resp.Body.Close()

	// Did not get a 200 OK response
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		log.Printf("Error sending result: %s", body)
		return
	}
}

func (c *RestClient) SendHeartbeat(workerId string) error {
	heartbeat := Heartbeat{WorkerId: workerId}
	jsonData, err := json.Marshal(heartbeat)
	if err != nil {
		return err
	}

	// TODO kill the worker if the heartbeat fails (404)
	// fmt.Println("Sending heartbeat to url: " + c.baseURL + "/worker/pulse")
	// fmt.Println(string(jsonData))
	resp, err := c.client.Post(c.baseURL+"/worker/pulse", "application/json", bytes.NewReader(jsonData))
	resp.Body.Close()
	return err
}
