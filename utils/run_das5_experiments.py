# This is a quick and dirty script to automate running experiments on DAS5. Note: ideally a SLURM job should probably
# contain the entire experiment setup (including master, worker, and query). Currently the script triggers multiple
# SLURM jobs and manages the experiment. Furthermore, the script should've been written differently (e.g., for writing
# to the result file a function could be used).

# Adjust the configuration below.
# Then run with: python3 ./utils/run_das5_experiments.py
# Or with debug logging: LOG_LEVEL=DEBUG python3 ./utils/run_das5_experiments.py


############################################
### CONFIGURE THE EXPERIMENT TO RUN HERE ###
############################################


default_experiment = {
    "query_iterations": 1,
    "n_workers": 1,
    "query_path": "datasets/query.fna",
    "target_path": "datasets/query.fna",
    "configuration": {
        "match_score": 2,
        "mismatch_penalty": 1,
        "gap_penalty": 1
    },
    "top_k": 5
}

experiment_configs = []

# The number of times to run a clean iteration, which means starting a fresh master, worker,
# and then executing the query. You might want to run multiple clean iterations such that
# the master's state does not affect the results.
clean_iterations = 1

# The number of times the query should be run within a single clean iteration.
# E.g., we start the master, worker, and then execute the query 5 times.
query_iterations = 2

# Configure the experiments to be run here (append them to the "experiment_configs" list).
for _ in range(clean_iterations):
    for n_workers in [1, 2]:
        exp = default_experiment.copy()
        exp["query_iterations"] = query_iterations
        exp["n_workers"] = n_workers
        experiment_configs.append(exp)


############################################
############################################
############################################


import subprocess, json, os, re, time, datetime, logging, sys

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),  # Set the log level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s [%(levelname)-8s] %(message)s'
)
logger = logging.getLogger(__name__)

class JSONFileContext:
    def __init__(self, file_path):
        self.file_path = file_path

    def __enter__(self):
        self.data = self.load_json()
        return self.data

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.save_json(self.data)

    def load_json(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def save_json(self, data):
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)

# The number of seconds to wait for all workers to connect to the master. If they do not connect in time, then the
# program classifies this experiment iteration as a failure.
WORKER_CONNECTION_TIMEOUT_SECONDS = 60


def exec_cmd(command): # e.g., ["ls", "-l"]
    return subprocess.run(command, capture_output=True, text=True)


def start_master():
    res = exec_cmd(["./utils/start_master.sh"])
    if (res.returncode != 0):
        return None

    ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', res.stdout)
    job_id_match = re.search(r'Submitted batch job (\d+)', res.stdout)

    return { "master_ip": ip_match.group(), "master_job_id": job_id_match.group(1)} if (ip_match and job_id_match) else None


def start_workers(num_workers, master_ip):
    res = exec_cmd(["./utils/start_worker.sh", str(num_workers), master_ip])
    if (res.returncode != 0):
        return None

    job_ids = re.findall(r'Submitted batch job (\d+)', res.stdout)
    job_ids_array = [int(job_id) for job_id in job_ids]

    return { "batch_job_ids": job_ids} if (job_ids) else None


def block_till_n_workers_connected(filepath, n_workers, timeout_seconds):
    start_time = time.time()
    target_pattern = r'Number of registered workers: {}'.format(n_workers)

    while True:
        if time.time() - start_time > timeout_seconds:
            return False
        try:
            with open(filepath, 'r') as file:
                file_contents = file.read()
                match = re.search(target_pattern, file_contents)
                if match:
                    return True
        except:
            return False
        time.sleep(1)


def start_query(experiment_config, master_ip, experiment_run_name, current_experiment_name):
    command = list(map(str, [
            "srun", "python3", "tui",
            "--output-path", f"results/{experiment_run_name}/{current_experiment_name}/",
            "--query", experiment_config["query_path"], "--database", experiment_config["target_path"],
            "--server-url", f"http://{master_ip}:8000",
            "--match-score", experiment_config["configuration"]["match_score"],
            "--mismatch-penalty", experiment_config["configuration"]["mismatch_penalty"],
            "--gap-penalty", experiment_config["configuration"]["gap_penalty"],
            "--top-k", experiment_config["top_k"]
        ]))
    res = exec_cmd(command)
    if (res.returncode != 0):
        return None

    elapsed_time = re.search(r'total elapsed time: ((\d+\.)*\d+) milliseconds', res.stdout).group(1).replace('.', '')
    computation_time = re.search(r'Computation time: ((\d+\.)*\d+) milliseconds', res.stdout).group(1).replace('.', '')

    return {
        "elapsed_time": int(elapsed_time),
        "computation_time": int(computation_time),
        "full_output": res.stdout
    } if (elapsed_time and computation_time) else None


def start_experiment(experiment_config, experiment_run_name):
    time_start = datetime.datetime.now()
    time_start_epoch = int(time_start.timestamp())
    time_start_readable = time_start.strftime("%Y-%m-%d_%H-%M-%S")
    num_workers = int(experiment_config["n_workers"])

    current_experiment_name = f"{time_start_readable}_{str(num_workers)}"

    result_file_path = f"result_{experiment_run_name}.json"

    # Set up meta results file if it doesnt exist.
    if not os.path.exists(result_file_path):
        with open(result_file_path, 'w') as file:
            json.dump({}, file, indent=4)

    # Add this experiment's parameters, commit id, etc.
    with JSONFileContext(result_file_path) as result_object:
        result_object[current_experiment_name] = {
            "experiment_config": experiment_config,
            "time_start_epoch": time_start_epoch,
            "time_start_readable": time_start_readable,
            "status": "STARTED"
        }

    # Set up started job ids (for tracking and cleaning).
    jobs_started = []
    query_res = None

    try:
        # Start master
        logger.debug("  Starting master...")
        master_res = start_master()
        if (master_res == None):
            raise Exception("Failed to start master")

        master_ip, master_job_id = master_res["master_ip"], master_res["master_job_id"]
        jobs_started.append(master_job_id)

        # Start worker(s)
        logger.debug(f"  Starting {num_workers} worker(s)...")
        workers_res = start_workers(num_workers, master_ip)
        if (workers_res == None):
            raise Exception("Failed to start workers")

        worker_job_ids = workers_res["batch_job_ids"]
        jobs_started.extend(worker_job_ids)

        # Write result to result file.
        with JSONFileContext(result_file_path) as result_object:
            result_object[current_experiment_name]["master_job_id"] = master_job_id
            result_object[current_experiment_name]["master_ip"] = master_ip
            result_object[current_experiment_name]["worker_job_ids"] = worker_job_ids

        # Wait until all workers have connected to the master.
        master_slurm_filepath = os.path.join(f"slurm-{master_job_id}.out")
        logger.debug("  Waiting for worker(s) to connect...")
        conn_res = block_till_n_workers_connected(master_slurm_filepath, experiment_config["n_workers"], WORKER_CONNECTION_TIMEOUT_SECONDS)
        if (conn_res == False):
            raise Exception(f"Workers did not connect to master within timelimit {WORKER_CONNECTION_TIMEOUT_SECONDS}")

        # Start query
        logger.debug("  Executing queries...")
        for i in range(experiment_config["query_iterations"]):
            logger.debug(f"    Query {i + 1}...")
            query_res = None # Resetting to None for the setting "status" property in the finally clause.
            query_res = start_query(experiment_config, master_ip, experiment_run_name, current_experiment_name)
            if (query_res == None):
                raise Exception("Query failed")

            # Write result to result file.
            with JSONFileContext(result_file_path) as result_object:
                if "result" not in result_object[current_experiment_name]:
                    result_object[current_experiment_name]["result"] = []
                current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                result_object[current_experiment_name]["result"].append({ "time": current_time, "query_res": query_res })

        logger.debug("  Success!")
    except KeyboardInterrupt:
        logger.critical(f"  Keyboard interrupt detected. Cleaning up and exiting...")
        sys.exit(1)
    except Exception as e:
        logger.error(f"  Experiment failed. Error: '{e}'. Cleaning up and continuing with next available experiment...")
    finally:
        time_end = datetime.datetime.now()
        time_end_epoch = int(time_end.timestamp())
        time_end_readable = time_end.strftime("%Y-%m-%d_%H-%M-%S")

        with JSONFileContext(result_file_path) as result_object:
            result_object[current_experiment_name]["status"] = "SUCCESS" if query_res != None else "FAILED"
            result_object[current_experiment_name]["time_end_readable"] = time_end_readable
            result_object[current_experiment_name]["time_end_epoch"] = time_end_epoch

        cleanup_experiment(jobs_started)


# To manually clean up all jobs associated with the account use: scancel -u <username>
def cleanup_experiment(job_ids):
    cancel_cmd = ["scancel"]
    cancel_cmd.extend(job_ids)
    logger.debug(f"  Cleaning up jobs: {', '.join(job_ids)}")
    res = exec_cmd(cancel_cmd)


def __main__():
    experiment_run_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    num_experiments = len(experiment_configs)
    for index, experiment_config in enumerate(experiment_configs):
        logger.info(f"Experiment {index + 1} out of {num_experiments}")
        start_experiment(experiment_config, experiment_run_name)


if __name__ == "__main__":
    __main__()
