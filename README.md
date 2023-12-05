# DLSA

Distributed Local Sequence Alignment

## Master

### Setup

Also check out the [DAS5](DAS5.md) setup instructions.

Python dependencies get managed by [Poetry](https://python-poetry.org/).
See https://python-poetry.org/docs/#installation for installation instructions.

After installing Poetry, you can install the project's dependencies using `poetry install`.

Run `poetry shell` to [activate](https://python-poetry.org/docs/basic-usage/#activating-the-virtual-environment) the virtual environment (in which the dependencies are installed).

### Usage

1. Run `python master/run.py` for hot reloading, otherwise run `python master/main.py`.
2. Go to `http://localhost:8000/docs` for the API documentation.

### Testing

Run `pytest master` inside the root directory.

## Worker

The worker runs in an infinite loop, which tries to register with the master node every 20 seconds. If the registration is successful, the worker starts sending a pulse to show the master it is alive every 8 seconds, the worker also enters another loop state in which it asks for work every 20 seconds. If it recieves work from the master, it iterates through every query-target pair it was tasked to calculate and performs the smith waterman algorithm. After it calculates the result of each pair, the worker immediately sends the result to the master such that if the worker were to shut down in the midst of calculations, the rest of the work could be delegated to another worker.

## Usage

To test the master and worker simultaneously you first have to run an instance of the master (see docs)

Once the master is up and running you can create a job by using the spawn_job.sh script, the request parameters can be modified to your liking.

`sh spawn_job.sh`

run the app with

`go run cmd/worker/main.go`
