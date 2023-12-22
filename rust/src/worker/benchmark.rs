use std::{
    sync::mpsc,
    time::{Duration, Instant},
};

use sw::algorithm::AlignmentScores;

pub fn run_benchmark(threshold: Duration, q_steps: i32, t_steps: i32) -> f32 {
    let n_q: i32 = 1 << 10;
    let mut n_t: i32 = 1 << 18;

    let mut i_q: i32 = 0;
    let mut sum: f32 = 0.0;

    n_t *= 2;
    n_t /= 1 << (q_steps + t_steps - 2);

    while i_q < q_steps {
        let mut i_t = 0;
        while i_t < t_steps {
            let (_, cups) = run_once(n_q << i_q, n_t << i_t, q_steps, t_steps);
            sum += cups;
            i_t += 1;
            // println!("nt:{}", n_t);
            // println!("i_t:{}", i_t);
        }
        i_q += 1;
    }
    return (sum as f32 / (n_q as f32 * n_t as f32)) as f32;
}

fn run_once(n_q: i32, n_t: i32, q_steps: i32, t_steps: i32) -> (u128, f32) {
    let scores = AlignmentScores {
        gap: -1,
        r#match: 2,
        miss: -1,
    };
    let query_sequence_chars: Vec<char> = (0..n_q).map(|_| 'A').collect();
    let target_sequence_chars: Vec<char> = (0..n_t).map(|_| 'A').collect();
    let start = Instant::now();
    let (_, _, _) = sw::algorithm::find_alignment_simd_lowmem::<64>(
        &query_sequence_chars,
        &target_sequence_chars,
        scores,
    );
    let duration = start.elapsed();
    let cups = n_q as f32 * n_t as f32 / duration.as_secs_f32() * 1e9;
    println!("q: {} t: {} cups: {}", n_q, n_t, cups);
    (duration.as_nanos(), cups)
}
