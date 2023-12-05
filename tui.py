import argparse
import json
import requests
import uuid
import io
import time
import os

descr_map = {
}

def parse_fasta(fasta_file_path):
    with open(fasta_file_path, 'r') as file:
        fasta_data = file.read()

    sequences = []
    entries = fasta_data.split('>')[1:]

    for entry in entries:
        lines = entry.strip().split('\n')
        seq_id = lines[0].split()[0]  # Assuming the first word is the ID
        seq_data = ''.join(lines[1:])
        id_ = str(uuid.uuid4())
        descr_map[id_] = seq_id
        sequences.append((id_, seq_data))

    return sequences



def send_to_server(query_files, target_files, server_url, match_score, mismatch_penalty, gap_penalty):
    content = {
        'queries': [],
    }
    for q_name,q_seq in query_files:
        for t_name,t_seq in target_files:
            content['queries'].append({
               'query': q_name,
                'target': t_name,
            })
    
    content['match_score'] = match_score
    content['mismatch_penalty'] = mismatch_penalty
    content['gap_penalty'] = gap_penalty
    
    body_content = json.dumps(content)
    combined_sequences = query_files + target_files

    sequences = query_files + target_files
    sequence_files = []
    for seq_name, seq_content in sequences:
        # Create a temporary file-like object for each sequence
        seq_file = io.BytesIO(str.encode(f'>{seq_name}\n{seq_content}\n'))
        # Use a UUID for a unique temporary file name
        seq_file_name = f"{seq_name}"
        sequence_files.append(('sequences', (seq_file_name, seq_file, 'application/octet-stream')))


    multipart_data = {
        'body': body_content,  
    }
    files = sequence_files 

    print(len(files))
    print(body_content)


    response = requests.post(server_url, data=multipart_data, files=files)

    
    for _, (_, file_obj, _) in sequence_files:
        file_obj.close()

    return response



def main():
    parser = argparse.ArgumentParser(description='Send FASTA sequences to a server.')
    parser.add_argument('--query', type=str, required=True, help='Path to query FASTA file')
    parser.add_argument('--database', type=str, required=True, help='Path to database FASTA file')
    parser.add_argument('--server-url', type=str, required=False, help='Server URL to send data to', default='http://localhost:8000')
    parser.add_argument('--output-path', type=str, required=False, help='Path to output file', default='results/')
    parser.add_argument('--match-score', type=str, required=False, help='Match score', default=2)
    parser.add_argument('--mismatch-penalty', type=str, required=False, help='Mismatch penalty', default=1)
    parser.add_argument('--gap-penalty', type=str, required=False, help='Gap score', default=1)

    args = parser.parse_args()

    sequences_query = parse_fasta(args.query)
    sequences_database = parse_fasta(args.database)
  

    #TODO: Send the scores and penalties to the server
    response = send_to_server(sequences_query,sequences_database, f'{args.server_url}/job/format/multipart', args.match_score, args.mismatch_penalty, args.gap_penalty)

    print(f'Server response: HTTP {response.status_code} - {response.text}')

    print (response.status_code)

    job_id = response.json()['id']
    print(f'Job ID: {job_id}')

    #if response is successful, poll for results
    curr_time = time.time()
    job_start = None
    computation_time = None
    if response.status_code == 200:
        print('Polling for results...')
        response = requests.get(f'{args.server_url}/job/{job_id}/status')
        print(f'Server response: HTTP {response.status_code} - {response.text}')
        while response.status_code == 200:
            if response.json()['state'] == 'IN_QUEUE':
                print ('Job in queue, waiting for it to start')
                time.sleep(2)
                response = requests.get(f'{args.server_url}/job/{job_id}/status')
                continue
            elif response.json()['state'] == 'IN_PROGRESS':
                if job_start is None:
                    job_start = time.time()
                total_elapsed_time = time.time() - curr_time
                print('Job not done yet, total elapsed time: ', int(total_elapsed_time), 'seconds')
                progress = response.json()['progress']
                print(f'Progress: {round(progress*100,2)}%')
                time.sleep(2)
                response = requests.get(f'{args.server_url}/job/{job_id}/status')
            else:
                total_elapsed_time = time.time() - curr_time
                computation_time = time.time() - job_start
                print('Job done, total elapsed time: ', int(total_elapsed_time), 'seconds')
                print('Computation time: ', int(computation_time), 'seconds')
                break
        # print('Job done')
        # print(response.json())
        computation_time = time.time() - job_start
        
        #TODO: Sort the results by score???

        response = requests.get(f'{args.server_url}/job/{job_id}/result')
        for result in response.json()['alignments']:
            query = descr_map[result['combination']['query']]
            target = descr_map[result['combination']['target']]
            results_dir = './results'
            os.makedirs(results_dir, exist_ok=True)  # This will create the directory if it does not exist

            file_path = os.path.join(results_dir, f'{query}.txt')  # Construct the file path

            if os.path.exists(file_path):
                mode = 'a'  # Append if the file exists
            else:
                mode = 'w'  # Create a new file if it does no
            
            # print(result)
            with open(file_path, mode) as file:
                file.write(f'>{target}\n')
                file.write(f'Aligment: {result["alignments"][0]["alignment"]}\n')
                file.write(f'Length: {result["alignments"][0]["length"]}\n')
                file.write(f'Score: {result["alignments"][0]["score"]}\n')
        print('result can be found in: results/')


if __name__ == '__main__':
    main()
