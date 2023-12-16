use std::{
    collections::HashMap,
    sync::{mpsc::Sender, Arc},
};
use sw::{algorithm::AlignmentScores, bindings::AlignmentResult};

use crate::{
    api::{Alignment, AlignmentDetail, TargetQueryCombination, WorkPackage, WorkResult},
    HashId, SharedMap, SharedState,
};
use rayon::prelude::*;
use std::error::Error;

const BUFFER_SIZE: usize = 100;

pub fn calculate_alignment_scores(
    work_package: &mut WorkPackage,
    shared_state: SharedMap,
    fetch_sender: Sender<String>, // Channel for fetch requests
    alignment_sender: Sender<AlignmentDetail>, // Channel for alignment details
) -> Result<(), Box<dyn Error>> {
    let scores = AlignmentScores {
        gap: work_package.gap_penalty,
        r#match: work_package.match_score,
        miss: work_package.mismatch_penalty,
    };

    //sort work_package.queries by descending length
    work_package
        .queries
        .sort_by(|a, b| (a.target.len() * a.query.len()).cmp(&(b.target.len() * &b.query.len())));

    // Using parallel iterators from rayon how easy is that??
    work_package.queries.par_iter().for_each(|query_target| {
        let query = &query_target.query;
        let target = &query_target.target;
        print!("Calculating alignment for: ");
        print!("{} {}", query, target);
        // Wait while data is being fetched by another thread
        let query_sequence = fetch_sequence(&shared_state, &fetch_sender, &query_target.query);
        let target_sequence = fetch_sequence(&shared_state, &fetch_sender, &query_target.target);
        // Wait while data is being fetched by another thread

        let target_sequence = match target_sequence {
            Some(sequence) => sequence,
            None => {
                println!("Could not fetch target sequence: {}", query_target.target);
                return;
            }
        };
        let query_sequence = match query_sequence {
            Some(sequence) => sequence,
            None => {
                println!("Could not fetch query sequence: {}", query_target.query);
                return;
            }
        };
        let target_sequence_chars: Vec<char> = target_sequence.chars().collect();
        let query_sequence_chars: Vec<char> = query_sequence.chars().collect();
        //TODO: fallback
        let (q_res, t_res, score) = sw::algorithm::find_alignment_simd_lowmem::<64>(
            &query_sequence_chars,
            &target_sequence_chars,
            scores,
        );
        let alignment = Alignment {
            alignment_string: q_res.iter().collect(),
            length: q_res.len() as i16,
            score: score,
        };
        //TODO: Need to somehow not copy (too much memory??)
        let combination = TargetQueryCombination {
            target: target.clone(),
            query: query.clone(),
        };
        let alignment_detail = AlignmentDetail {
            alignment: alignment,
            combination: combination,
        };
        alignment_sender.send(alignment_detail).unwrap();
    });
    Ok(())
}

//Function to fetch sequence from shared map
fn fetch_sequence(
    shared_state: &SharedMap,
    fetch_sender: &Sender<String>,
    key: &String,
) -> Option<Arc<String>> {
    println!("Shared state: {:?}", shared_state);
    let (lock, cvar) = &**shared_state;
    let mut shared = lock.lock().unwrap();

    while shared.is_fetching {
        println!("Waiting for fetch to complete");
        shared = cvar.wait(shared).unwrap();
    }
    println!("Shared map: {:?}", shared.map);

    if !shared.map.contains_key(key) {
        print!("Fetching sequence for: {}", key);
        shared.is_fetching = true;

        fetch_sender.send(key.clone()).unwrap();
        shared.is_fetching = false;
        cvar.notify_all();
    }

    assert!(shared.map.contains_key(key));
    shared.map.get(key).cloned()
}
