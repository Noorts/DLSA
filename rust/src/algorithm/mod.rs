use argminmax::ArgMinMax;
use spin_sync::Barrier;
use std::{
    cmp::{max, min},
    simd::Simd,
    sync::Arc,
    thread,
};

use crate::{
    find_alignment_simd,
    utils::{self, coord, index},
};

use std::simd::prelude::{SimdInt, SimdOrd, SimdPartialEq};

#[derive(Copy, Clone)]
#[repr(C)]
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
            if y > target.len() + x {
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
        .into_iter()
        .map(|x| *x as u16 + 2)
        .chain(std::iter::repeat(0))
        .take(query_size)
        .collect();

    // Padding the target to the next whole number of LANES
    let target_size = utils::roundup(target.len(), LANES);
    let target: Vec<_> = target
        .into_iter()
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
        .map(Simd::<u16, LANES>::from_slice)
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

            let max = r_query_skip
                .simd_max(r_target_skip)
                .simd_max(r_match_mis)
                .simd_max(zero_splat);

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

pub fn find_alignment_simd_lowmem<const LANES: usize>(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
) -> (Vec<char>, Vec<char>, i16)
where
    std::simd::LaneCount<LANES>: std::simd::SupportedLaneCount,
{
    // Unless we make the diagonals, the normal algorithms will be faster
    if target.len() < 2 * query.len() {
        return find_alignment_simd(query, target, scores);
    }

    let mut total_target_result = Vec::new();
    let mut total_query_result = Vec::new();

    // Padding the query to the next whole number of LANES
    let query_size = utils::roundup(query.len(), LANES);
    let query_u16: Vec<_> = query
        .into_iter()
        .map(|x| *x as u16 + 1)
        .chain(std::iter::repeat(0))
        .take(query_size)
        .collect();

    // Padding the target to the next whole number of LANES
    let target_u16: Vec<_> = target.into_iter().map(|x| *x as u16 + 1).collect();

    let width = query_u16.len() + 1;
    assert!(query_u16.len() >= query.len());
    let data_height = target.len() + query.len() + 1;
    // TODO: Fix trunc div error
    let wrapping_height = query_u16.len()
        + ((query_u16.len() * scores.r#match.unsigned_abs() as usize)
            / scores.gap.unsigned_abs() as usize);

    let data_store_height = wrapping_height + width;

    let mut data: Vec<i16> = vec![0; width * data_store_height];
    let mut current_max = 0;

    // No need to wrap the indices here as the the height is guaranteed to be at least `width`
    // high
    for y in 2..width {
        for x in 1..y {
            if y - x >= target_u16.len() {
                continue;
            }

            let sub_score = if query_u16[x - 1] == target_u16[y - x - 1] {
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
        let left = index(1, y, width);
        let (_, row_max_index) = (&data[left..left + width - 1]).argminmax();
        let row_max = data[left + row_max_index];

        // PERF: Probably better to do this for the entire diagonal part in one run.
        if row_max > current_max {
            current_max = row_max;
            let (max_x, _y) = coord(left + row_max_index, width);

            // PERF: We should benchmark if using `with_capacity` is cheaper or not
            // This should be done with realistic workloads!
            total_target_result = Vec::with_capacity(wrapping_height);
            total_query_result = Vec::with_capacity(wrapping_height);
            traceback_wrapping(
                &data,
                query,
                target,
                max_x,
                y,
                width,
                &mut total_query_result,
                &mut total_target_result,
                scores,
            )
        }
    }

    let gap_splat = Simd::<i16, LANES>::splat(scores.gap);
    let match_splat = Simd::<i16, LANES>::splat(scores.r#match);
    let mis_splat = Simd::<i16, LANES>::splat(scores.miss);
    let zero_splat = Simd::<i16, LANES>::splat(0);
    let one_splat = Simd::<i16, LANES>::splat(1);

    let mut target_rev = target_u16.clone();
    target_rev.reverse();

    let query_vecs = query_u16
        .chunks_exact(LANES)
        .map(Simd::<u16, LANES>::from_slice)
        .collect::<Vec<_>>();

    for y in width..(target_u16.len() + 2) {
        let mut row_0_i = index(1, y % data_store_height, width);
        let mut row_1_i = index(1, (y - 1) % data_store_height, width);
        let mut row_2_i = index(1, (y - 2) % data_store_height, width);
        let mut start_x = 1;
        let mut target_rev_start = target_u16.len() - (y - start_x);
        let mut row_max = 0;
        for lane_index in 0..(query_u16.len() / LANES) {
            let query_vec = query_vecs[lane_index];
            let target_vec = Simd::<u16, LANES>::from_slice(
                &target_rev[target_rev_start..target_rev_start + LANES],
            );

            // GAP
            let r_query_skip =
                Simd::<i16, LANES>::from_slice(&data[row_1_i..row_1_i + LANES]) + gap_splat;

            let r_target_skip =
                Simd::<i16, LANES>::from_slice(&data[row_1_i - 1..row_1_i - 1 + LANES]) + gap_splat;

            let mask = query_vec.simd_eq(target_vec).to_int().cast::<i16>();

            let pos_mask = mask.abs();
            let neg_mask = mask + one_splat;

            let mismatch_vec = (match_splat * pos_mask) + (mis_splat * neg_mask);

            let r_match_mis =
                Simd::<i16, LANES>::from_slice(&data[row_2_i - 1..row_2_i - 1 + LANES])
                    + mismatch_vec;

            let max = r_query_skip
                .simd_max(r_target_skip)
                .simd_max(r_match_mis)
                .simd_max(zero_splat);

            data[row_0_i..row_0_i + LANES].copy_from_slice(max.as_ref());

            row_0_i += LANES;
            row_1_i += LANES;
            row_2_i += LANES;

            start_x += LANES;
            target_rev_start += LANES;

            row_max = row_max.max(max.reduce_max());
        }

        if row_max > current_max {
            current_max = row_max;
            let left = index(1, y % data_store_height, width);
            let (_argmin, argmax) = (&data[left..left + width - 1]).argminmax();
            let (x, _y) = coord(left + argmax, width);

            // PERF: We should benchmark if using `with_capacity` is cheaper or not
            // This should be done with realistic workloads!
            total_target_result = Vec::with_capacity(wrapping_height);
            total_query_result = Vec::with_capacity(wrapping_height);
            traceback_wrapping(
                &data,
                query,
                target,
                x,
                y,
                width,
                &mut total_query_result,
                &mut total_target_result,
                scores,
            );
        }
    }

    // TODO: Error is problably in cases where the two diagonals overlap
    let mut start_x = 2;
    for y in (target.len() + 2)..data_height {
        for x in start_x..query.len() + 1 {
            assert!(y - x - 1 <= target.len());

            if x + 1 > y {
                continue;
            }

            let sub_score = if query_u16[x - 1] == target_u16[y - x - 1] {
                scores.r#match
            } else {
                scores.miss
            };

            data[index(x, y % data_store_height, width)] = max(
                max(
                    data[index(x, (y - 1) % data_store_height, width)] + scores.gap, // Skip query
                    data[index(x - 1, (y - 1) % data_store_height, width)] + scores.gap, // Skip in target
                ),
                max(
                    data[index(x - 1, (y - 2) % data_store_height, width)] + sub_score, // Take or mis
                    0,                                                                  // Minimum
                ),
            );
        }

        let left = index(start_x, y % data_store_height, width);
        let right = index(query.len() + 1, y % data_store_height, width);
        assert_ne!(left, right);
        let (_argmin, argmax) = (&data[left..right]).argminmax();
        let row_max = data[argmax + left];
        if row_max > current_max {
            current_max = row_max;
            let (max_x, _max_y) = coord(left + argmax, width);

            assert!(_max_y == y % data_store_height);
            assert!(max_x >= start_x);

            // PERF: We should benchmark if using `with_capacity` is cheaper or not
            // This should be done with realistic workloads!
            total_target_result = Vec::with_capacity(wrapping_height);
            total_query_result = Vec::with_capacity(wrapping_height);
            traceback_wrapping(
                &data,
                query,
                target,
                max_x,
                y,
                width,
                &mut total_query_result,
                &mut total_target_result,
                scores,
            )
        }

        start_x += 1;
    }

    (total_query_result, total_target_result, current_max)
}

pub fn string_scores_parallel(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
    threads: usize,
) -> Vec<i16> {
    let width = query.len() + 1;
    let height = query.len() + target.len() + 1;

    let threads = min(threads, query.len());

    let mut data = Vec::with_capacity(width * height);

    let data_ptr = SendPtr(data.as_mut_ptr());

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

                for y in 2..height {
                    for x in left..right {
                        if x >= y {
                            continue;
                        }
                        if y > target.len() + x {
                            continue;
                        }

                        let sub_score = if query[x - 1] == target[y - x - 1] {
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

pub fn traceback_wrapping(
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
    if x == 0 || y == 0 || x == y {
        return;
    }

    let data_store_height = data.len() / width;

    let match_score = if query[x - 1] == target[y - x - 1] {
        scores.r#match
    } else {
        scores.miss
    };

    // TODO: Evaluate what is more important in the case of multiple paths
    let score = data[index(x, y % data_store_height, width)];
    if score == 0 {
        return;
    } else if score == data[index(x - 1, (y - 2) % data_store_height, width)] + match_score {
        traceback_wrapping(
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
    } else if score == data[index(x - 1, (y - 1) % data_store_height, width)] + scores.gap {
        traceback_wrapping(
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
    } else if score == data[index(x, (y - 1) % data_store_height, width)] + scores.gap {
        traceback_wrapping(
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
            "Mismatch in data at {x}, {y} with q: {} t: {}; rel_y: {}; data_store_height: {data_store_height}",
            query[x - 1],
            target[y - x - 1],
            y % data_store_height,
        );
    }
}

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
    if x == 0 || y == 0 || x == y {
        return;
    }

    // println!("{x} {y}");
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
