use core::hash;
use std::{
    collections::HashMap,
    mem,
    sync::{mpsc::Sender, Arc},
};
use sw::algorithm::AlignmentScores;
pub mod benchmark;

use crate::api::{
    Alignment, AlignmentDetail, Sequence, SequenceId, TargetQueryCombination, WorkPackage,
};
use rayon::prelude::*;
use std::error::Error;

pub fn calculate_alignment_scores(
    // work_package: &mut WorkPackage,
    work_package: &mut WorkPackage,
    hash_map: &HashMap<SequenceId, Sequence>,
    // shared_state: SharedMap,
    // fetch_sender: Sender<String>, // Channel for fetch requests
    alignment_sender: &Sender<AlignmentDetail>, // Channel for alignment details
) -> Result<(), Box<dyn Error>> {
    let scores = AlignmentScores {
        gap: -work_package.gap_penalty,
        r#match: work_package.match_score,
        miss: -work_package.mismatch_penalty,
    };

    //sort work_package.queries by descending length
    work_package
        .queries
        .sort_by(|a, b| (a.target.len() * a.query.len()).cmp(&(b.target.len() * &b.query.len())));
    // Using parallel iterators from rayon how easy is that??
    let pairs = work_package.queries.par_iter().for_each(|query_target| {
        let query_id = &query_target.query;
        let target_id = &query_target.target;
        let query = &hash_map[query_id];
        let target = &hash_map[target_id];

        let target_sequence_chars: Vec<char> = query.chars().collect();
        let query_sequence_chars: Vec<char> = target.chars().collect();
        //TODO: fallback
        let (q_res, t_res, score, _, _) = sw::algorithm::find_alignment_simd_lowmem::<64>(
            &query_sequence_chars,
            &target_sequence_chars,
            scores,
        );
        let alignment = Alignment {
            alignment: q_res.iter().collect(),
            length: q_res.len() as i16,
            score: score,
        };
        let combination = TargetQueryCombination {
            target: target_id.clone(),
            query: query_id.clone(),
        };
        let alignment_detail = AlignmentDetail {
            alignment: alignment,
            combination: combination,
        };
        alignment_sender.send(alignment_detail).unwrap();
        // alignment_sender.send(alignment_detail).unwrap();
    });
    Ok(())
}
//Function to fetch sequence from shared map
// fn fetch_sequence(
//     shared_state: &SharedMap,
//     fetch_sender: &Sender<String>,
//     key: &String,
// ) -> Option<Arc<String>> {
//     println!("Shared state: {:?}", shared_state);
//     let (lock, cvar) = &**shared_state;
//     let mut shared = lock.lock().unwrap();

//     while shared.is_fetching {
//         shared = cvar.wait(shared).unwrap();
//     }

//     if !shared.map.contains_key(key) {
//         shared.is_fetching = true;

//         fetch_sender.send(key.clone()).unwrap();
//         shared.is_fetching = false;
//         cvar.notify_all();
//     }

//     assert!(shared.map.contains_key(key));
//     shared.map.get(key).cloned()
// }
