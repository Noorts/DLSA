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
const protocolPrefix = "http://"
const defaultMasterNodeAddress = "0.0.0.0:8000" // Default address and port of the master node.
const retryDelayGetWorkInSeconds = 1

func main() {
	masterNodeAddress := defaultMasterNodeAddress

	// To supply the master node address via the CLI run: `go run cmd/worker/main.go -- 192.168.0.1:8000`.
	if len(os.Args) == 3 && regexp.MustCompile(ipv4WithPortRegex).MatchString(os.Args[2]) {
		masterNodeAddress = os.Args[2]
		log.Printf("Master node address: %v", protocolPrefix+masterNodeAddress)
	} else {
		log.Printf("Master node address not passed. Falling back to default. %v", protocolPrefix+masterNodeAddress)
	}

	log.Printf("Benchmarking worker...")
	benchmark := smithwaterman.Benchmark(time.Duration(1e7), 4, 2)
	client := worker.InitRestClient(protocolPrefix + masterNodeAddress)

	// Create a new worker instance with the machine specs, the worker ID is null
	w := worker.InitWorker(client, benchmark)
	_, err := w.RegisterWorker()
	if err != nil {
		log.Printf("Error registering worker: %v", err)
		return
	}

	mcpus := float64(benchmark) / 1e6
	//if we registered successfully, we request work
	log.Printf("Worker registered (%.0f GCUPS). Waiting for work...", mcpus)

	for {
		runtime.GC()
		work, err := w.GetWork()

		if err != nil {
			log.Printf("Error fetching work: %v", err)
			time.Sleep(retryDelayGetWorkInSeconds * time.Second)
			continue
		}

		// If there is no work available, we wait for a bit and try again
		if work == nil {
			time.Sleep(retryDelayGetWorkInSeconds * time.Second)
			continue
		}

		log.Printf("Got work. Start calculating alignments...")
		log.Printf("Calculating %d queries", len(work.Queries))
		w.ExecuteWork(work)
		log.Printf("Done calculating alignments.")
		log.Printf("Waiting for work...")
	}
}
