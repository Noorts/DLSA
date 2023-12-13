use std::iter::repeat;
#[allow(unused_imports)]
use sw::algorithm::{
    string_scores_parallel, string_scores_simd, string_scores_straight, traceback,
};

use argminmax::ArgMinMax;

const LANES: usize = 64;

use sw::{
    algorithm::AlignmentScores,
    utils::{coord, roundup},
};

fn main() {
    let scores = AlignmentScores {
        gap: -2,
        r#match: 3,
        miss: -3,
    };

    let mut query = repeat('A').take(128).collect::<Vec<_>>();
    let mut target = repeat('T').take(20000000).collect::<Vec<_>>();

    target[67] = 'Z';
    target[68] = 'Z';
    query[13] = 'Z';
    query[14] = 'Z';

    let start = std::time::Instant::now();

    let data = string_scores_simd::<LANES>(&query, &target, scores);

    // PERF: We might be able to eek out a bit more perf here by ignoring the min in a custom
    // implementation
    let (_min_index, max_index) = data.argminmax();
    let max = data[max_index];
    // let (max_index, max) = data.iter().enumerate().max_by_key(|(_, x)| *x).unwrap();

    let end = std::time::Instant::now();

    let duration = end - start;
    println!("Query * Target: {}", query.len() * target.len());
    println!("Duration: {:?}", duration.as_micros());

    println!(
        "MCUPS: {}",
        (query.len() * target.len()) / (duration.as_micros() as usize)
    );

    println!("Max: {}", max);
    println!("Max index: {}", max_index);
    let data_width = roundup(query.len(), LANES) + 1;
    let (x, y) = coord(max_index, data_width);
    println!("x: {}; y: {}", x - 1, y - x);
    let mut query_result = Vec::new();
    let mut target_result = Vec::new();

    traceback(
        &data,
        &query,
        &target,
        x,
        y,
        data_width,
        &mut query_result,
        &mut target_result,
        scores,
    );

    println!("Query: {:?}", query_result);
    println!("Target: {:?}", target_result);
}
