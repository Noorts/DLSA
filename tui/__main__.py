import argparse
import io
import json
import os
import sys
import time
import uuid

import requests

descr_map = {}

PRINT_UNIT = "milliseconds"
PRINT_UNIT_FROM_NANO_RATIO = 1_000_000


def parse_fasta(fasta_file_path):
    with open(fasta_file_path, "r") as file:
        fasta_data = file.read()

    sequences = []
    entries = fasta_data.split(">")[1:]

    for entry in entries:
        lines = entry.strip().split("\n")
        seq_id = lines[0].split()[0]
        seq_data = "".join(lines[1:])
        id_ = str(uuid.uuid4())
        descr_map[id_] = seq_id
        sequences.append((id_, seq_data))

    return sequences


def send_to_server(query_files, target_files, server_url, match_score, mismatch_penalty, gap_penalty):
    content = {
        "queries": [],
    }
    for q_name, q_seq in query_files:
        for t_name, t_seq in target_files:
            content["queries"].append(
                {
                    "query": q_name,
                    "target": t_name,
                }
            )

    content["match_score"] = match_score
    content["mismatch_penalty"] = mismatch_penalty
    content["gap_penalty"] = gap_penalty

    body_content = json.dumps(content)

    sequences = query_files + target_files
    sequence_files = []
    for seq_name, seq_content in sequences:
        seq_file = io.BytesIO(seq_content.encode())
        sequence_files.append(("sequences", (seq_name, seq_file, "application/octet-stream")))

    multipart_data = {
        "body": body_content,
    }
    files = sequence_files

    # print(len(files))
    # print(body_content)

    response = requests.post(server_url, data=multipart_data, files=files)

    for _, (_, file_obj, _) in sequence_files:
        file_obj.close()

    return response


def update_progress(progress):
    bar_length = 50  # Modify this to change the length of the progress bar
    if progress >= 1:
        progress = 1

    block = int(round(bar_length * progress))
    progress_text = "{:.2f}%".format(progress * 100)
    # Ensure the progress text is always the same length
    progress_text = progress_text.ljust(7, " ")

    text = "\rProgress: [{0}] {1}".format("#" * block + "-" * (bar_length - block), progress_text)
    sys.stdout.write(text)
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Send FASTA sequences to a server.")
    parser.add_argument("--query", type=str, required=True, help="Path to query FASTA file")
    parser.add_argument("--database", type=str, required=True, help="Path to database FASTA file")
    parser.add_argument(
        "--server-url", type=str, required=False, help="Server URL to send data to", default="http://localhost:8000"
    )
    parser.add_argument("--output-path", type=str, required=False, help="Path to output file", default="results/")
    parser.add_argument("--match-score", type=str, required=False, help="Match score", default=2)
    parser.add_argument("--mismatch-penalty", type=str, required=False, help="Mismatch penalty", default=1)
    parser.add_argument("--gap-penalty", type=str, required=False, help="Gap penalty", default=1)
    parser.add_argument("--top-k", type=int, required=False, help="Top k query matches", default=None)

    args = parser.parse_args()

    sequences_query = parse_fasta(args.query)
    sequences_database = parse_fasta(args.database)

    # TODO: Send the scores and penalties to the server
    response = send_to_server(
        sequences_query,
        sequences_database,
        f"{args.server_url}/job/format/multipart",
        args.match_score,
        args.mismatch_penalty,
        args.gap_penalty,
    )

    # print(f'Server response: HTTP {response.status_code} - {response.text}')

    # print (response.status_code)

    job_id = response.json()["id"]
    # print(f'Job ID: {job_id}')

    # if response is successful, poll for results
    curr_time = time.time_ns()
    job_start = None
    if response.status_code == 200:
        # print('Polling for results...')
        response = requests.get(f"{args.server_url}/job/{job_id}/status")
        print(f"Job Successfully submitted, job ID: {job_id}")
        while response.status_code == 200:
            if response.json()["state"] == "IN_QUEUE":
                sys.stdout.write("Job in queue, waiting for it to start\r")
                sys.stdout.flush()
                time.sleep(0.1)
                response = requests.get(f"{args.server_url}/job/{job_id}/status")
                continue
            elif response.json()["state"] == "IN_PROGRESS":
                if job_start is None:
                    job_start = time.time_ns()
                progress = response.json()["progress"]
                update_progress(progress)
                time.sleep(0.1)
                response = requests.get(f"{args.server_url}/job/{job_id}/status")
            else:
                if job_start is None:
                    job_start = time.time_ns()
                    total_elapsed_time = time.time_ns() - job_start
                update_progress(1.0)
                total_elapsed_time = time.time_ns() - curr_time
                computation_time = time.time_ns() - job_start

                print(
                    f"\nJob done - total elapsed time: {int(total_elapsed_time / PRINT_UNIT_FROM_NANO_RATIO):,} {PRINT_UNIT}".replace(
                        ",", "."
                    )
                )
                # print(
                #     f"Computation time: {int(computation_time / PRINT_UNIT_FROM_NANO_RATIO):,} {PRINT_UNIT}".replace(
                #         ",", "."
                #     )
                # )
                break
        top_k_map = {}

        response = requests.get(f"{args.server_url}/job/{job_id}/result")
        print(f"Computation time: {response.json()['computation_time']} seconds")
        for result in response.json()["alignments"]:
            query = descr_map[result["combination"]["query"]]
            target = descr_map[result["combination"]["target"]]
            score = result["alignments"][0]["score"]
            length = result["alignments"][0]["length"]
            alignment = result["alignments"][0]["alignment"]
            if query not in top_k_map:
                top_k_map[query] = []
                top_k_map[query].append((target, score, length, alignment))
            else:
                top_k_map[query].append((target, score, length, alignment))

        top_k_map = {k: sorted(v, key=lambda x: x[1], reverse=True) for k, v in top_k_map.items()}
        if args.top_k is not None:
            top_k_map = {k: v[: args.top_k] for k, v in top_k_map.items()}

        for query, results in top_k_map.items():
            if args.output_path is not None:
                results_dir = args.output_path
            else:
                results_dir = "../results"
            os.makedirs(results_dir, exist_ok=True)

            file_path = os.path.join(results_dir, f"{query}.txt")
            if os.path.exists(file_path):
                mode = "a"
            else:
                mode = "w"

            with open(file_path, mode) as file:
                for target, score, length, alignment in results:
                    file.write(f">{target}\n")
                    file.write(f"Alignment: {alignment}\n")
                    file.write(f"Length: {length}\n")
                    file.write(f"Score: {score}\n")
                    file.write("\n")

        print(f"Result can be found in: {results_dir}")


if __name__ == "__main__":
    main()
