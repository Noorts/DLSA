use regex::Regex;

use std::error::Error;
use std::mem;
use std::{collections::HashMap, env};
mod api;
mod worker;
use std::sync::mpsc;

use api::{
    AlignmentDetail, CompleteWorkPackage, MachineSpecs, RestClient, Sequence, SequenceId,
    WorkResult,
}; // Import RestClient from the api module

#[allow(unused_imports)]
use sw::algorithm::{
    string_scores_simd, string_scores_straight, traceback,
};

use crate::api::WorkPackage;
use crate::worker::benchmark::run_benchmark;
use crate::worker::calculate_alignment_scores;

const LANES: usize = 64;

#[derive(Hash)]
struct HashId {
    id: String,
}

fn main() {
    //MPSC channel for sending work results to master node
    const BUFFER_SIZE: usize = 50;

    let args: Vec<String> = env::args().collect();
    let ipv4_with_port_regex = Regex::new(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$").unwrap();
    let default_master_node_address = "0.0.0.0:8000";
    let protocol_prefix = "http://";
    let retry_delay_get_work_in_seconds = 1;

    //channels for synchronization
    // let (alignment_sender, alignment_receiver) = mpsc::channel();

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

    println!("Master node address: {}", master_node_address);
    let client = RestClient::new(format!("{}{}", protocol_prefix, master_node_address));

    //TODO: benchmark and send ncpus
    let cpus = num_cpus::get();
    println!("Number of cpus: {}", cpus);
    let cups: f32 = run_benchmark(std::time::Duration::from_secs(1), 2, 4);
    let cups_int = cups as i32;
    println!("MCUPS: {}", cups_int);
    let worker_id = client
        .register_worker(MachineSpecs {
            benchmark_result: cups_int,
        })
        .unwrap();
    println!("Successfully registered worker with id: {}", worker_id);

    //Loop untel work is available
    let (alignment_sender, alignment_receiver) = mpsc::channel();
    let (id_sender, id_receiver) = mpsc::channel();

    //Spawn a thread to handle the results
    let client_clone = RestClient::new(format!("{}{}", protocol_prefix, master_node_address));
    std::thread::spawn(move || {
        handle_results(
            &alignment_receiver,
            BUFFER_SIZE,
            &client_clone,
            &id_receiver,
        );
    });

    //Spawn a thread to send heartbeats
    let worker_id_clone: String = worker_id.clone();
    let client_clone: RestClient =
        RestClient::new(format!("{}{}", protocol_prefix, master_node_address));

    std::thread::spawn(move || loop {
        match client_clone.send_pulse(&worker_id_clone) {
            Ok(_) => {
                println!("Successfully sent heartbeat");
            }
            Err(e) => {
                println!("Failed to send heartbeat: {}", e);
            }
        }
        std::thread::sleep(std::time::Duration::from_secs(4));
    });

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
                println!("Failed to get work: {}", e);
                panic!("Failed to get work")
            }
            Ok(Some(mut work_package)) => {
                if let Some(id) = work_package.id.clone() {
                    id_sender
                        .send((id.clone(), work_package.queries.len()))
                        .expect("Failed to send id");

                    match get_all_sequences(&mut work_package, &client, &worker_id) {
                        Ok(mut complete_work_package) => {
                            let scores = calculate_alignment_scores(
                                &mut complete_work_package.work_package,
                                &complete_work_package.sequences,
                                &alignment_sender,
                            );
                            //(TODO: why would I need this?)clear all the variables
                            // complete_work_package.work_package.queries.clear();
                            // complete_work_package.sequences.clear();
                            // complete_work_package.work_package.id = None;
                            // mem::drop(complete_work_package);

                            println!("Scores: {:?}", scores);
                        }
                        Err(e) => {
                            println!("Failed to fetch all sequences: {}", e);
                        }
                    };
                } else {
                    print!("Work package has no ID")
                }
            } // worker.run
        }
    }
}
//When buffer is full send results to master node
pub fn handle_results(
    receiver: &mpsc::Receiver<AlignmentDetail>,
    buffer_size: usize,
    client: &RestClient,
    id_receiver: &mpsc::Receiver<(String, usize)>,
) {
    let mut result_buffer: Vec<AlignmentDetail> = Vec::with_capacity(buffer_size);
    let mut current_id: Option<String> = None;
    let mut total_sequences = 0;
    let mut recv_count = 0;
    loop {
        // Check for a new ID
        if let Ok((id, count)) = id_receiver.try_recv() {
            current_id = Some(id);
            total_sequences = count;
            recv_count = 0;
            print!("Got new ID: {}", current_id.clone().unwrap());
        }

        if let Ok(received) = receiver.try_recv() {
            result_buffer.push(received);
            recv_count += 1;

            if result_buffer.len() >= buffer_size {
                // Replace the buffer with a new, empty Vec and pass the old buffer
                let work_result = WorkResult {
                    alignments: mem::replace(&mut result_buffer, Vec::with_capacity(buffer_size)),
                };

                match client.send_work_result(work_result, &current_id.clone().unwrap()) {
                    Ok(_) => {
                        println!("Successfully sent buffered work result");
                    }
                    Err(e) => {
                        println!("Failed to send work result: {}", e);
                    }
                }
                result_buffer.clear();
                // No need to clear result_buffer as it's now a new, empty Vec
            }
            //Send final batch
            if recv_count >= total_sequences {
                let work_result = WorkResult {
                    alignments: mem::replace(&mut result_buffer, Vec::with_capacity(buffer_size)),
                };

                match client.send_work_result(work_result, &current_id.clone().unwrap()) {
                    Ok(_) => {
                        println!("Successfully sent buffered work result");
                    }
                    Err(e) => {
                        println!("Failed to send work result: {}", e);
                    }
                }
                result_buffer.clear();
                // No need to clear result_buffer as it's now a new, empty Vec
            }
        }
    }
}

fn get_all_sequences<'a>(
    work_package: &'a mut WorkPackage,
    client: &RestClient,
    worker_id: &str,
) -> Result<CompleteWorkPackage<'a>, Box<dyn Error>> {
    let mut sequences: HashMap<SequenceId, Sequence> = HashMap::new(); // Counter for received items
    for query_target in &work_package.queries {
        let query = &query_target.query;
        let target = &query_target.target;
        let work_id = work_package.id.as_ref().ok_or("Work ID is missing")?;
        if !sequences.contains_key(query) {
            let sequence = client.get_sequence(work_id, query, worker_id);
            // println!("Got sequence: {:?}", sequence);
            sequences.insert(query.clone(), sequence.unwrap());
        }
        if !sequences.contains_key(target) {
            let sequence = client.get_sequence(work_id, target, worker_id);
            sequences.insert(target.clone(), sequence.unwrap());
        }
    }
    println!("Got all sequences ");
    return Ok(CompleteWorkPackage {
        work_package: work_package,
        sequences: sequences,
    });
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
