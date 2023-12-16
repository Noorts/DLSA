use rand::Rng;
use regex::Regex;
use std::mem;
use std::{collections::HashMap, env};
mod api;
mod worker;
use std::sync::{mpsc, Arc, Condvar, Mutex};

use api::{AlignmentDetail, MachineSpecs, RestClient, WorkResult}; // Import RestClient from the api module
use sw::{
    algorithm::{find_alignment_simd_lowmem, AlignmentScores},
    find_alignment_simd,
};

#[allow(unused_imports)]
use sw::algorithm::{
    string_scores_parallel, string_scores_simd, string_scores_straight, traceback,
};

use crate::api::WorkPackage;
use crate::worker::calculate_alignment_scores;

const LANES: usize = 64;

#[derive(Hash)]
struct HashId {
    id: String,
}

#[derive(Debug)]
struct SharedState {
    map: HashMap<Arc<String>, Arc<String>>,
    is_fetching: bool,
    condvar: Condvar,
}
type SharedMap = Arc<(Mutex<SharedState>, Condvar)>;

fn main() {
    //MPSC channel for sending work results to master node
    const BUFFER_SIZE: usize = 200;

    let args: Vec<String> = env::args().collect();
    let ipv4_with_port_regex = Regex::new(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$").unwrap();
    let default_master_node_address = "0.0.0.0:8000";
    let protocol_prefix = "http://";
    let retry_delay_get_work_in_seconds = 1;

    //channels for synchronization
    let (fetch_sender, fetch_receiver) = mpsc::channel();
    let (alignment_sender, alignment_receiver) = mpsc::channel();

    let master_node_address = if args.len() > 1 {
        let arg = &args[1];
        if ipv4_with_port_regex.is_match(arg) {
            arg
        } else {
            default_master_node_address
        }
    } else {
        default_master_node_address
    };

    //maps for storing queries and targets
    let shared_map: SharedMap = Arc::new((
        Mutex::new(SharedState {
            map: HashMap::new(),
            is_fetching: false,
            condvar: Condvar::new(),
        }),
        Condvar::new(),
    ));

    println!("Master node address: {}", master_node_address);
    let client = RestClient::new(format!("{}{}", protocol_prefix, master_node_address));

    //TODO: benchmark

    let worker_id = client
        .register_worker(MachineSpecs {
            benchmark_result: 2000.0,
        })
        .unwrap();
    println!("Successfully registered worker with id: {}", worker_id);

    //Loop untel work is available
    loop {
        match client.get_work(&worker_id) {
            Ok(None) => {
                // No work available, wait for a while
                println!(
                    "No work available, waiting for {} seconds",
                    retry_delay_get_work_in_seconds
                );
                std::thread::sleep(std::time::Duration::from_secs(
                    retry_delay_get_work_in_seconds,
                ));
            }
            Err(e) => {
                // Handle error
            }
            Ok(Some(mut work_package)) => {
                println!("Got work package: {:?}", work_package);
                calculate_alignment_scores(
                    &mut work_package,
                    shared_map.clone(),
                    fetch_sender.clone(),
                    alignment_sender.clone(),
                );

                // Check if there are any fetch requests to process
                while let Ok(request) = fetch_receiver.try_recv() {
                    println!("Got fetch request: {}", request);
                    process_fetch_request(
                        &request,
                        &client,
                        &shared_map,
                        &work_package,
                        &worker_id,
                    );
                }

                // Handle alignment details, potentially in a separate thread or after all fetch requests are processed
                handle_results(
                    &alignment_receiver,
                    BUFFER_SIZE,
                    &client,
                    work_package.id.unwrap(),
                );
            }
        }
        // worker.run
    }
}

//When buffer is full send results to master node
pub fn handle_results(
    receiver: &mpsc::Receiver<AlignmentDetail>,
    buffer_size: usize,
    client: &RestClient,
    id: String,
) {
    let mut result_buffer: Vec<AlignmentDetail> = Vec::with_capacity(buffer_size);

    for received in receiver {
        result_buffer.push(received);

        if result_buffer.len() >= buffer_size {
            // Replace the buffer with a new, empty Vec and pass the old buffer
            let work_result = WorkResult {
                alignments: mem::replace(&mut result_buffer, Vec::with_capacity(buffer_size)),
            };
            client.send_work_result(work_result, &id);
            // No need to clear result_buffer as it's now a new, empty Vec
        }
    }

    if !result_buffer.is_empty() {
        let work_result = WorkResult {
            alignments: result_buffer,
        };
        client.send_work_result(work_result, &id);
    }
}

// This function is called for each fetch request
fn process_fetch_request(
    request: &String,
    client: &RestClient,
    shared_map: &SharedMap,
    work_package: &WorkPackage,
    worker_id: &str,
) {
    let seq = match client.get_sequence(
        work_package.id.clone().unwrap(),
        request.clone(),
        worker_id.to_string(),
    ) {
        Ok(sequence) => sequence,
        Err(e) => {
            eprintln!("Failed to fetch sequence for request {}: {}", request, e);
            return;
        }
    };

    let (lock, _cvar) = &**shared_map;
    let mut shared = lock.lock().unwrap(); // Consider handling the PoisonError here
    shared.map.insert(Arc::new(request.clone()), Arc::new(seq));
}

// fn oldmain() {
//     let scores = AlignmentScores {
//         gap: -2,
//         r#match: 3,
//         miss: -3,
//     };

//     let mut rng = rand::thread_rng();

//     let charset = ['A', 'T', 'C', 'G'];

//     for _i in 0..10000 {
//         let query: Vec<_> = (0..)
//             .map(|_| {
//                 let i: u8 = rng.gen();
//                 let char = charset[i as usize % charset.len()];

//                 char
//             })
//             .take(1000)
//             .collect();

//         let target: Vec<_> = (0..)
//             .map(|_| {
//                 let i: u8 = rng.gen();
//                 let char = charset[i as usize % charset.len()];

//                 char
//             })
//             .take(1000)
//             .collect();

//         let lm = find_alignment_simd_lowmem::<LANES>(&query, &target, scores);
//         let sd = find_alignment_simd::<LANES>(&query, &target, scores);

//         assert_eq!(lm, sd);
//     }
// }
