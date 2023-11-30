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



def send_to_server(query_files, target_files, server_url):
    content = {
        'queries': [],
    }
    for q_name,q_seq in query_files:
        for t_name,t_seq in target_files:
            content['queries'].append({
               'query': q_name,
                'target': t_name,
            })
      
    
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


    response = requests.post(server_url, data=multipart_data, files=files)

    
    for _, (_, file_obj, _) in sequence_files:
        file_obj.close()

    return response



def main():
    parser = argparse.ArgumentParser(description='Send FASTA sequences to a server.')
    parser.add_argument('--query', type=str, required=True, help='Path to query FASTA file')
    parser.add_argument('--database', type=str, required=True, help='Path to database FASTA file')
    parser.add_argument('--server-url', type=str, required=True, help='Server URL to send data to')

    args = parser.parse_args()

    sequences_query = parse_fasta(args.query)
    sequences_database = parse_fasta(args.database)
    
    # Send the data to the server
    response = send_to_server(sequences_query,sequences_database, f'{args.server_url}/job/format/multipart')

    print(f'Server response: HTTP {response.status_code} - {response.text}')

    job_id = response.json()['id']
    print(f'Job ID: {job_id}')

    #if response is successful, poll for results
    if response.status_code == 200:
        print('Polling for results...')
        response = requests.get(f'{args.server_url}/job/{job_id}/result')
        print(f'Server response: HTTP {response.status_code} - {response.text}')
        while response.status_code == 404:
              if response.json()['detail'] == 'Job not done yet':
                print('Job not done yet')
                time.sleep(2)
                response = requests.get(f'{args.server_url}/job/{job_id}/result')

        print('Job done')
        print(response.json())
        for result in response.json()['alignments']:
            query = descr_map[result['combination']['query']]
            target = descr_map[result['combination']['target']]
            results_dir = './results'
            os.makedirs(results_dir, exist_ok=True)  # This will create the directory if it does not exist

            file_path = os.path.join(results_dir, f'{query}.txt')  # Construct the file path

            if os.path.exists(file_path):
                mode = 'a'  # Append if the file exists
            else:
                mode = 'w'  # Create a new file if it does not
            print('result')
            print(result)
            with open(file_path, mode) as file:
                file.write(f'>{target}\n')
                file.write(f'Aligment: {result["alignments"][0]["alignment"]}\n')
                file.write(f'Length: {result["alignments"][0]["length"]}\n')
                file.write(f'Score: {result["alignments"][0]["score"]}\n')


if __name__ == '__main__':
    main()
