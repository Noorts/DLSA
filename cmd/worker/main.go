package main

import (
	"dlsa/internal/worker"
	"log"
	"time"
)

func main() {

	//TODO: URL of master node
	baseURL := "http://0.0.0.0:8000"
	client := worker.InitRestClient(baseURL)

	// Create a new worker instance with the machine specs, the worker ID is null
	w, err := worker.InitWorker(client)
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
			//The worker waits for 20 seconds before trying to register again
			time.Sleep(20 * time.Second) // Sleeps for 2 seconds

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
				time.Sleep(20 * time.Second) // Sleeps for 2 seconds
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
