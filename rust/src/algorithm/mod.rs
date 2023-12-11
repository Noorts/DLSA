use spin_sync::Barrier;
use std::{
    cmp::{max, min},
    simd::Simd,
    sync::Arc,
    thread,
};

use crate::utils::{self, index};

use std::simd::prelude::{SimdPartialEq, SimdOrd, SimdInt};

#[derive(Copy, Clone)]
pub struct AlignmentScores {
    pub gap: i16,
    pub r#match: i16,
    pub miss: i16,
}

// Underlying functions
pub fn string_scores_sequential(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
) -> Vec<i16> {
    let width = query.len() + 1;
    let height = query.len() + target.len() + 1;
    let mut data: Vec<i16> = vec![0; width * (width + height)];

    for y in 1..height {
        for x in 1..width {
            if x >= y {
                continue;
            }
            if y > target.len() + x - 1 {
                continue;
            }
            let lhs = query[x - 1];
            let rhs = target[y - x];

            let sub_score = if lhs == rhs {
                scores.r#match
            } else {
                scores.miss
            };

            data[index(x, y, width)] = max(
                max(
                    data[index(x, y - 1, width)] + scores.gap,     // Skip query
                    data[index(x - 1, y - 1, width)] + scores.gap, // Skip in target
                ),
                max(
                    data[index(x - 1, y - 2, width)] + sub_score, // Take or mis
                    0,                                            // Minimum
                ),
            );
        }
    }

    data
}

pub fn string_scores_simd<const LANES: usize>(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
) -> Vec<i16>
where
    std::simd::LaneCount<LANES>: std::simd::SupportedLaneCount,
{
    // Padding the query to the next whole number of LANES
    let query_size = utils::roundup(query.len(), LANES);
    let query: Vec<_> = query
        .iter()
        .map(|x| *x as u16 + 2)
        .chain(std::iter::repeat(0))
        .take(query_size)
        .collect();

    // Padding the target to the next whole number of LANES
    let target_size = utils::roundup(target.len(), LANES);
    let target: Vec<_> = target
        .iter()
        .map(|x| *x as u16 + 2)
        .chain(std::iter::repeat(1))
        .take(target_size)
        .collect();

    let width = query.len() + 1;
    let data_height = query.len() + target.len() + 1;
    let mut data: Vec<i16> = vec![0; width * (width + data_height)];

    for y in 2..width {
        for x in 1..y {
            if y - x >= target.len() {
                continue;
            }

            let sub_score = if query[x - 1] == target[y - x - 1] {
                scores.r#match
            } else {
                scores.miss
            };

            data[index(x, y, width)] = max(
                max(
                    data[index(x, y - 1, width)] + scores.gap,     // Skip query
                    data[index(x - 1, y - 1, width)] + scores.gap, // Skip in target
                ),
                max(
                    data[index(x - 1, y - 2, width)] + sub_score, // Take or mis
                    0,                                            // Minimum
                ),
            );
        }
    }

    let gap_splat = Simd::<i16, LANES>::splat(scores.gap);
    let match_splat = Simd::<i16, LANES>::splat(scores.r#match);
    let mis_splat = Simd::<i16, LANES>::splat(scores.miss);
    let zero_splat = Simd::<i16, LANES>::splat(0);
    let one_splat = Simd::<i16, LANES>::splat(1);

    let mut target_rev = target.clone();
    target_rev.reverse();

    let query_vecs = query
        .chunks_exact(LANES)
        .map(|x| Simd::<u16, LANES>::from_slice(x))
        .collect::<Vec<_>>();

    for y in width..=(target.len() + 1) {
        let mut i = index(1, y, width);
        let mut start_x = 1;
        let mut target_rev_start = target.len() - (y - start_x);
        for lane_index in 0..(query.len() / LANES) {
            let query_vec = query_vecs[lane_index];
            let target_vec = Simd::<u16, LANES>::from_slice(
                &target_rev[target_rev_start..target_rev_start + LANES],
            );

            // GAP
            let r_query_skip =
                Simd::<i16, LANES>::from_slice(&data[(i - width)..(i - width + LANES)]) + gap_splat;

            let r_target_skip =
                Simd::<i16, LANES>::from_slice(&data[(i - width - 1)..(i - width - 1 + LANES)])
                    + gap_splat;

            let mask = query_vec.simd_eq(target_vec).to_int().cast::<i16>();

            let pos_mask = mask.abs();
            let neg_mask = mask + one_splat;

            let mismatch_vec = (match_splat * pos_mask) + (mis_splat * neg_mask);

            let r_match_mis = Simd::<i16, LANES>::from_slice(
                &data[(i - 2 * width - 1)..(i - 2 * width - 1 + LANES)],
            ) + mismatch_vec;

            let r_gaps = r_query_skip.simd_max(r_target_skip);
            let r_match_mis_floor = r_match_mis.simd_max(zero_splat);

            let max = r_gaps.simd_max(r_match_mis_floor);

            data[i..(i + LANES)].copy_from_slice(max.as_ref());

            i += LANES;
            start_x += LANES;
            target_rev_start += LANES;
        }
    }

    for y in (data_height - width)..data_height {
        for x in 1..width {
            if x + 1 > y {
                continue;
            }
            if y - x >= target.len() {
                continue;
            }

            let sub_score = if query[x - 1] == target[y - x - 1] {
                scores.r#match
            } else {
                scores.miss
            };

            data[index(x, y, width)] = max(
                max(
                    data[index(x, y - 1, width)] + scores.gap,     // Skip query
                    data[index(x - 1, y - 1, width)] + scores.gap, // Skip in target
                ),
                max(
                    data[index(x - 1, y - 2, width)] + sub_score, // Take or mis
                    0,                                            // Minimum
                ),
            );
        }
    }

    data
}

pub fn string_scores_parallel(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
    threads: usize,
) -> Vec<i16> {
    let width = query.len() + 1;
    let height = query.len() + target.len() + 1;

    let mut data = Vec::with_capacity(width * height);

    let data_ptr = SendPtr {
        0: data.as_mut_ptr(),
    };

    let barrier = Arc::new(Barrier::new(threads));

    thread::scope(|s| {
        let handles = (0..threads).map(|thread_index| {
            let left = thread_index * (width - 1) / threads + 1;
            let right = (thread_index + 1) * (width - 1) / threads + 1;

            let c = Arc::clone(&barrier);

            let child = s.spawn(move || {
                let _ = &data_ptr;
                let data_ref =
                    unsafe { std::slice::from_raw_parts_mut(data_ptr.0, width * height) };

                for y in 1..height {
                    let max_x = min(right, y);
                    for x in left..max_x {
                        // HOT LOOP
                        // PERF: Probably faster to kickstart the top and bottom
                        // On a single thread and save ourselves the branching
                        // inside the hot loop

                        if target.len() + x - 1 < y {
                            continue;
                        }

                        let sub_score = if query[x - 1] == target[y - x] {
                            scores.r#match
                        } else {
                            scores.miss
                        };

                        data_ref[index(x, y, width)] = max(
                            max(
                                data_ref[index(x, y - 1, width)] + scores.gap, // Skip query
                                data_ref[index(x - 1, y - 1, width)] + scores.gap, // Skip in target
                            ),
                            max(
                                data_ref[index(x - 1, y - 2, width)] + sub_score, // Take or mis
                                0,                                                // Minimum
                            ),
                        );
                    }

                    c.wait();
                }
            });

            child
        });

        // TODO: Probably not necessary anymore due to the thread scope
        for handle in handles.collect::<Vec<_>>() {
            handle.join().unwrap();
        }
    });

    data
}

pub fn string_scores_straight(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
) -> Vec<i16> {
    let width = query.len() + 1;
    let height = target.len() + 1;
    let mut data: Vec<i16> = vec![0; width * height];

    for y in 1..height {
        for x in 1..width {
            let sub_score = if query[x - 1] == target[y - 1] {
                scores.r#match
            } else {
                scores.miss
            };

            data[index(x, y, width)] = max(
                max(
                    data[index(x, y - 1, width)] + scores.gap, // Skip query
                    data[index(x - 1, y, width)] + scores.gap, // Skip in target
                ),
                max(
                    data[index(x - 1, y - 1, width)] + sub_score, // Take or mis
                    0,                                            // Minimum
                ),
            );
        }
    }

    data
}

#[derive(Copy, Clone)]
struct SendPtr<T>(*mut T);

unsafe impl<T> Send for SendPtr<T> {}

pub fn traceback(
    data: &[i16],
    query: &[char],
    target: &[char],
    x: usize,
    y: usize,
    width: usize,
    query_result: &mut Vec<char>,
    target_result: &mut Vec<char>,
    // Maybe take a reference instead of a copy because of the recursive nature
    // Or maybe just make it iterative
    scores: AlignmentScores,
) {
    if x == 0 || y == 0 {
        return;
    }

    println!("{x} {y}");
    let match_score = if query[x - 1] == target[y - x - 1] {
        scores.r#match
    } else {
        scores.miss
    };

    // TODO: Evaluate what is more important in the case of multiple paths
    let score = data[index(x, y, width)];
    if score == 0 {
        return;
    } else if score == data[index(x - 1, y - 2, width)] + match_score {
        traceback(
            data,
            query,
            target,
            x - 1,
            y - 2,
            width,
            query_result,
            target_result,
            scores,
        );
        query_result.push(query[x - 1]);
        target_result.push(target[y - x - 1]);
    } else if score == data[index(x - 1, y - 1, width)] + scores.gap {
        traceback(
            data,
            query,
            target,
            x - 1,
            y - 1,
            width,
            query_result,
            target_result,
            scores,
        );
        query_result.push(query[x - 1]);
        target_result.push('-');
    } else if score == data[index(x, y - 1, width)] + scores.gap {
        traceback(
            data,
            query,
            target,
            x,
            y - 1,
            width,
            query_result,
            target_result,
            scores,
        );
        query_result.push('-');
        target_result.push(target[y - x - 1]);
    } else {
        panic!(
            "Mismatch in data at {x}, {y} with q: {} t: {}",
            query[x - 1],
            target[y - x - 1]
        );
    }
}

pub fn traceback_straight(
    data: &[i16],
    query: &[char],
    target: &[char],
    x: usize,
    y: usize,
    width: usize,
    query_result: &mut Vec<char>,
    target_result: &mut Vec<char>,
    scores: AlignmentScores,
) {
    if x == 0 || y == 0 {
        return;
    }

    let match_score = if query[x - 1] == target[y - 1] {
        scores.r#match
    } else {
        scores.miss
    };

    let score = data[index(x, y, width)];
    if score == 0 {
        return;
    } else if score == data[index(x - 1, y - 1, width)] + match_score {
        traceback_straight(
            data,
            query,
            target,
            x - 1,
            y - 1,
            width,
            query_result,
            target_result,
            scores,
        );
        query_result.push(query[x - 1]);
        target_result.push(target[y - 1]);
    } else if score == data[index(x - 1, y, width)] + scores.gap {
        traceback_straight(
            data,
            query,
            target,
            x - 1,
            y,
            width,
            query_result,
            target_result,
            scores,
        );
        query_result.push(query[x - 1]);
        target_result.push('-');
    } else if score == data[index(x, y - 1, width)] + scores.gap {
        traceback_straight(
            data,
            query,
            target,
            x,
            y - 1,
            width,
            query_result,
            target_result,
            scores,
        );
        query_result.push('-');
        target_result.push(target[y - 1]);
    } else {
        panic!("Mismatch in data");
    }
}
