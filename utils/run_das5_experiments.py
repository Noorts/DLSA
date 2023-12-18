# This is a quick and dirty script to automate running experiments on DAS5. Note: ideally a SLURM job should probably
# contain the entire experiment setup (including master, worker, and query). Currently the script triggers multiple
# SLURM jobs and manages the experiment. Furthermore, the script should've been written differently (e.g., for writing
# to the result file a function could be used).

# Run with: python3 ./utils/run_das5_experiments.py
# Or debug: LOG_LEVEL=DEBUG python3 ./utils/run_das5_experiments.py

import subprocess, json, os, re, time, datetime, logging, sys

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),  # Set the log level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s [%(levelname)-8s] %(message)s'
)
logger = logging.getLogger(__name__)

default_experiment = {
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

# Add the experiment to be run here.
iterations = 10
for _ in range(iterations):
    for n_workers in [1, 2, 4, 8]:
        exp = default_experiment.copy()
        exp["n_workers"] = n_workers
        experiment_configs.append(exp)


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

    meta_file_path = f"result_{experiment_run_name}.json"

    # Set up meta results file if it doesnt exist.
    if not os.path.exists(meta_file_path):
        with open(meta_file_path, 'w') as file:
            json.dump({}, file, indent=4)

    # Add this experiment's parameters, commit id, etc.
    with open(meta_file_path, 'r') as file:
        meta_object = json.load(file)

    meta_object[current_experiment_name] = {
        "experiment_config": experiment_config,
        "time_start_epoch": time_start_epoch,
        "time_start_readable": time_start_readable,
        "status": "STARTED"
    }

    with open(meta_file_path, 'w') as file:
        json.dump(meta_object, file, indent=4)

    # Set up started job ids (for tracking and cleaning).
    jobs_started = []
    query_res = None

    try:
        # Start master
        logger.debug("Starting master...")
        master_res = start_master()
        if (master_res == None):
            logger.error("Failed to start master. Exiting...")
            return

        master_ip, master_job_id = master_res["master_ip"], master_res["master_job_id"]
        jobs_started.append(master_job_id)

        # Start worker(s)
        logger.debug(f"Starting {num_workers} worker(s)...")
        workers_res = start_workers(num_workers, master_ip)
        if (workers_res == None):
            logger.error("Failed to start workers. Exiting...")
            cleanup_experiment(jobs_started)
            return

        worker_job_ids = workers_res["batch_job_ids"]
        jobs_started.extend(worker_job_ids)

        # Write result to result file.
        with open(meta_file_path, 'r') as file:
            meta_object = json.load(file)

        meta_object[current_experiment_name]["master_job_id"] = master_job_id
        meta_object[current_experiment_name]["master_ip"] = master_ip
        meta_object[current_experiment_name]["worker_job_ids"] = worker_job_ids

        with open(meta_file_path, 'w') as file:
            json.dump(meta_object, file, indent=4)

        # Wait until X workers have connected.
        timeout_seconds = 60
        master_slurm_filepath = os.path.join(f"slurm-{master_job_id}.out")
        logger.debug("Waiting for workers to connect...")
        conn_res = block_till_n_workers_connected(master_slurm_filepath, experiment_config["n_workers"], timeout_seconds)
        if (conn_res == False):
            logger.error(f"Workers did not connect to master within timelimit {timeout_seconds}. Exiting...")
            cleanup_experiment(jobs_started)
            return

        # Start query
        logger.debug("Executing query...")
        query_res = start_query(experiment_config, master_ip, experiment_run_name, current_experiment_name)
        if (query_res == None):
            logger.error("Query failed. Exiting...")
            cleanup_experiment(jobs_started)
            return

        elapsed_time, computation_time = query_res["elapsed_time"], query_res["computation_time"]

        logger.debug("Success!")
    except KeyboardInterrupt:
        logger.critical(f"Keyboard interrupt detected. Cleaning up and exiting...")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Experiment failed. Error: '{e}'. Cleaning up and continuing with next available experiment...")
    finally:
        # Write result to result file.
        with open(meta_file_path, 'r') as file:
            meta_object = json.load(file)

        time_end = datetime.datetime.now()
        time_end_epoch = int(time_end.timestamp())
        time_end_readable = time_end.strftime("%Y-%m-%d_%H-%M-%S")

        if query_res != None:
            meta_object[current_experiment_name]["result"] = query_res
            meta_object[current_experiment_name]["status"] = "SUCCESS"
        else:
            meta_object[current_experiment_name]["status"] = "FAILED"
        meta_object[current_experiment_name]["time_end_readable"] = time_end_readable
        meta_object[current_experiment_name]["time_end_epoch"] = time_end_epoch

        with open(meta_file_path, 'w') as file:
            json.dump(meta_object, file, indent=4)

        cleanup_experiment(jobs_started)


# To manually clean up all jobs associated with the account use: scancel -u <username>
def cleanup_experiment(job_ids):
    cancel_cmd = ["scancel"]
    cancel_cmd.extend(job_ids)
    logger.debug(f"Cleaning up jobs: {', '.join(job_ids)}")
    res = exec_cmd(cancel_cmd)


def __main__():
    experiment_run_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    num_experiments = len(experiment_configs)
    for index, experiment_config in enumerate(experiment_configs):
        logger.info(f"Experiment {index + 1} out of {num_experiments}")
        start_experiment(experiment_config, experiment_run_name)


if __name__ == "__main__":
    __main__()
