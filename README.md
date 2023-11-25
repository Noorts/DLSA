# DLSA

Distributed Local Sequence Alignment

## Master

### Setup

Python dependencies get managed by [Poetry](https://python-poetry.org/).
See https://python-poetry.org/docs/#installation for installation/usage instructions.

### Usage

Run `python master/run.py` for hot reloading, otherwise run `python master/main.py`.

Go to `http://localhost:8000/docs` for the API documentation.

### Testing

Run `pytest master` inside the root directory.

## Worker

The worker runs in an infite loop, which tries to register with the master node every 20 seconds. If the registration is successful, the worker starts sending a pulse to show the master it is alive every 8 seconds, the worker also enters another loop state in which it asks for work every 20 seconds. If it recieves work from the master, it iterates through every query-target pair it was tasked to calculate and performs the smith waterman algorithm. After it calculates the result of each pair, the worker immediately sends the result to the master such that if the worker were to shut down in the midst of calculations, the rest of the work could be delegated to another worker.

## Usage

To test the master and worker simultaneously you first have to run an instance of the master (see docs)

To create a job on the master you can use the spawn_job.sh script, the request parameters can be modified to your liking.

`sh spawn_job.sh`

run the app with

`go run cmd/worker/main.go`
