package main

import (
	"dlsa/internal/smithwaterman"
	"dlsa/internal/worker"
	"log"
	"os"
	"regexp"
	"runtime"
	"time"
)

const ipv4WithPortRegex = `^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$` // Note: does not include `localhost`.
const protocolPrefix = "http://"                                         // TODO: Can we use HTTPS?
const defaultMasterNodeAddress = "0.0.0.0:8000"                          // Default address and port of the master node.
const retryDelayRegisterWorkerInSeconds = 20
const retryDelayGetWorkInSeconds = 20

func main() {
	masterNodeAddress := defaultMasterNodeAddress

	// To supply the master node address via the CLI run: `go run cmd/worker/main.go -- 192.168.0.1:8000`.
	if len(os.Args) == 3 && regexp.MustCompile(ipv4WithPortRegex).MatchString(os.Args[2]) {
		masterNodeAddress = os.Args[2]
		log.Printf("The address of the master node was passed as a CLI argument. %v", protocolPrefix+masterNodeAddress)
	} else {
		log.Printf("The address of the master node was not passed. Falling back to default. %v", protocolPrefix+masterNodeAddress)
	}

	benchmark := smithwaterman.Benchmark(time.Duration(1e7), 4, 2)

	runtime.GC()

	if benchmark != 0 {
		log.Printf("Benchmark: %v", benchmark)
	}

	client := worker.InitRestClient(protocolPrefix + masterNodeAddress)

	// Create a new worker instance with the machine specs, the worker ID is null
	w, err := worker.InitWorker(client, benchmark)
	if err != nil {
		log.Fatalf("Error creating worker: %v", err)
	} else {
		log.Printf("Initialized worker: %+v", w)
	}

	//Loop to register the worker
	for {
		_, err := w.RegisterWorker()
		if err != nil {
			log.Printf("Error registering worker: %v", err)
			//The worker waits for X seconds before trying to register again
			time.Sleep(retryDelayRegisterWorkerInSeconds * time.Second)

			continue
		} else {
			log.Printf("Registered worker: %+v", w)
		}
		//if we registered successfully, we request work
		//TODO: Have some kind of stopping criteria, max tries or something
		for {
			work, err := w.GetWork()
			//TODO: Should there be a response from the server that says I will never have work for you?
			if err != nil {
				log.Printf("Error fetching task: %v", err)
				time.Sleep(retryDelayGetWorkInSeconds * time.Second)
				continue
			}

			if work == nil {
				log.Printf("No work available")
				time.Sleep(retryDelayGetWorkInSeconds * time.Second)
				continue
			}

			_, err = w.ExecuteWork(work)

			if err != nil {
				log.Printf("Error executing task: %v", err)
				continue
			}
		}
	}
}
