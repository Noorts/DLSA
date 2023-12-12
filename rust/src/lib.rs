#![feature(portable_simd, stdsimd, test)]
use argminmax::ArgMinMax;
extern crate test;

use algorithm::{
    string_scores_parallel, string_scores_sequential, string_scores_simd, string_scores_straight,
    traceback, traceback_straight, AlignmentScores,
};
use utils::coord;

use crate::utils::index;
pub mod algorithm;
pub mod bindings;

const SCORES: AlignmentScores = AlignmentScores {
    gap: -2,
    r#match: 3,
    miss: -3,
};

type AlignResult = (Vec<char>, Vec<char>, i16);

pub fn find_alignment_sequential(query: &[char], target: &[char]) -> AlignResult {
    let data = string_scores_sequential(query, target, SCORES);
    let mut query_result = Vec::with_capacity(query.len());
    let mut target_result = Vec::with_capacity(target.len());

    let width = query.len() + 1;
    // TODO: Find max index
    if let Some((index, _value)) = data.iter().enumerate().max_by_key(|(_i, x)| *x) {
        let (x, y) = coord(index, width);
        traceback_straight(
            &data,
            query,
            target,
            x,
            y,
            width,
            &mut query_result,
            &mut target_result,
            SCORES,
        );
    }

    (query_result, target_result, 0)
}

pub fn find_alignment_sequential_straight(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
) -> AlignResult {
    let data = string_scores_straight(query, target, scores);
    let mut query_result = Vec::with_capacity(query.len());
    let mut target_result = Vec::with_capacity(target.len());
    visualize_straight(&data, query, target);

    let width = query.len() + 1;
    // TODO: Find max index
    if let Some((index, _value)) = data.iter().enumerate().max_by_key(|(_i, x)| *x) {
        let (x, y) = coord(index, width);
        traceback_straight(
            &data,
            query,
            target,
            x,
            y,
            width,
            &mut query_result,
            &mut target_result,
            SCORES,
        );
    }

    (query_result, target_result, 0)
}

pub fn find_alignment_parallel(query: &[char], target: &[char], threads: usize) -> AlignResult {
    let data = string_scores_parallel(query, target, SCORES, threads);
    let mut query_result = Vec::with_capacity(query.len());
    let mut target_result = Vec::with_capacity(target.len());

    let width = query.len() + 1;
    // TODO: Find max index
    if let Some((index, _value)) = data.iter().enumerate().max_by_key(|(_i, x)| *x) {
        let (x, y) = coord(index, width);
        traceback(
            &data,
            query,
            target,
            x,
            y,
            width,
            &mut query_result,
            &mut target_result,
            SCORES,
        );
    }

    (query_result, target_result, 0)
}

pub fn find_alignment_simd<const LANES: usize>(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
) -> AlignResult
where
    std::simd::LaneCount<LANES>: std::simd::SupportedLaneCount,
{
    let data = string_scores_simd::<LANES>(query, target, scores);

    let data_width = utils::roundup(query.len(), LANES) + 1;
    let _data_height = utils::roundup(target.len(), LANES) + 1;

    let mut query_result = Vec::with_capacity(query.len());
    let mut target_result = Vec::with_capacity(target.len());

    // TODO: Find max index
    let (_min_index, max_index) = data.argminmax();
    let (x, y) = coord(max_index, data_width);
    traceback(
        &data,
        query,
        target,
        x,
        y,
        data_width,
        &mut query_result,
        &mut target_result,
        scores,
    );


    (query_result, target_result, data[max_index])
}

pub mod utils {
    #[inline(always)]
    pub fn index(x: usize, y: usize, width: usize) -> usize {
        y * width + x
    }

    #[inline(always)]
    pub fn coord(index: usize, width: usize) -> (usize, usize) {
        return (index % width, index / width);
    }

    #[inline(always)]
    pub fn roundup(number: usize, multiple: usize) -> usize {
        if multiple == 0 {
            return number;
        }

        let remainder = number % multiple;

        if remainder == 0 {
            return number;
        }

        return number + (multiple - remainder);
    }
}

#[allow(dead_code)]
fn visualize_straight(data: &[i16], query: &[char], target: &[char]) {
    let width = query.len() + 1;
    let height = target.len() + 1;

    print!("    ");
    for letter in query {
        print!("  {}  ", letter);
    }

    println!("");

    for y in 1..height {
        print!(" {} ", target[y - 1]);
        for x in 1..width {
            print!(" {:3} ", data[index(x, y, width)]);
        }
        println!("");
    }
}

#[allow(dead_code)]
fn visualize(data: &[i16], query: &[char], target: &[char]) {
    let width = query.len() + 1;
    let height = target.len() + 1;

    print!("    ");
    for letter in query {
        print!("  {}  ", letter);
    }

    println!("");

    for y in 1..height + width {
        print!(
            " {} ",
            if y - 1 < target.len() {
                target[y - 1]
            } else {
                '-'
            }
        );
        for x in 1..width {
            print!(" {:3} ", data[index(x, y + x - 1, width)]);
        }
        println!("");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::utils::*;

    const LANES: usize = 64;

    #[test]
    fn test_roundup() {
        assert_eq!(roundup(5, 0), 5);
        assert_eq!(roundup(5, 1), 5);
        assert_eq!(roundup(5, 3), 6);
        assert_eq!(roundup(0, 3), 0);
        assert_eq!(roundup(6, 3), 6);
    }

    #[test]
    fn test_index_coord_consistency() {
        for width in 3..100 {
            for x in 0..width {
                for y in 0..100 {
                    let (x2, y2) = coord(index(x, y, width), width);
                    eprintln!("{} {} {}", x, y, width);
                    assert_eq!(x, x2);
                    assert_eq!(y, y2);
                }
            }
        }
    }

    fn alignment_tester_simd(
        q_in: &str,
        t_in: &str,
        q_out: &str,
        t_out: &str,
        scores: AlignmentScores,
    ) {
        let q_in = &q_in.chars().collect::<Vec<_>>();
        let t_in = &t_in.chars().collect::<Vec<_>>();
        let q_out = &q_out.chars().collect::<Vec<_>>();
        let t_out = &t_out.chars().collect::<Vec<_>>();
        let res = find_alignment_simd::<LANES>(&q_in, &t_in, scores);
        assert_eq!(&res.0, q_out);
        assert_eq!(&res.1, t_out);
    }

    // #[test]
    // fn test_find_alignment_straight() {
    //     let scores = AlignmentScores {
    //         gap: -1,
    //         r#match: 2,
    //         mis: -1,
    //     };
    //     let res = find_alignment_sequential_straight(&['h', 'o', 'i'], &['h', 'o', 'i'], scores);
    //     assert_eq!(&res.0, &['h', 'o', 'i']);
    // }
    //
    // #[test]
    // fn test_find_alignment_parallel() {
    //     let res = find_alignment_parallel(&['h', 'o', 'i'], &['h', 'o', 'i'], 1);
    //     assert_eq!(&res.0, &['h', 'o', 'i']);
    // }

    #[test]
    fn test_find_alignment_simd() {
        let scores = AlignmentScores {
            gap: -1,
            r#match: 2,
            miss: -1,
        };
        // Basic
        alignment_tester_simd("a", "a", "a", "a", scores);
        alignment_tester_simd("hoi", "hoi", "hoi", "hoi", scores);
        alignment_tester_simd("ho", "hoi", "ho", "ho", scores);

        // Long cases
        {
            // Long target
            let query = "abc";
            let target = std::iter::repeat('z')
                .take(1000)
                .chain("abc".chars())
                .chain(std::iter::repeat('z').take(1000))
                .collect::<String>();
            alignment_tester_simd(query, &target, "abc", "abc", scores);
        }

        {
            // Both long
            let query = std::iter::repeat('x')
                .take(1000)
                .chain("abc".chars())
                .chain(std::iter::repeat('x').take(500))
                .collect::<String>();
            let target = std::iter::repeat('z')
                .take(2000)
                .chain("abc".chars())
                .chain(std::iter::repeat('z').take(1000))
                .collect::<String>();

            alignment_tester_simd(&query, &target, "abc", "abc", scores);
        }

        {
            // Both long
            let query = std::iter::repeat('x')
                .take(1000)
                .chain("abc".chars())
                .chain(std::iter::repeat('x').take(500))
                .collect::<String>();
            let target = std::iter::repeat('z')
                .take(2000)
                .chain("ac".chars())
                .chain(std::iter::repeat('z').take(1000))
                .collect::<String>();

            alignment_tester_simd(&query, &target, "abc", "a-c", scores);
        }

        // No match

        // Gap
        {
            let scores = AlignmentScores {
                gap: -2,
                r#match: 3,
                miss: -3,
            };
            alignment_tester_simd("Hoi", "HHii", "Hoi", "H-i", scores);
        }

        // Mismatch
        alignment_tester_simd(
            "TACGGGCCCGCTAC",
            "TAGCCCTATCGGTCA",
            "TACGGGCCCGCTA-C",
            "TA---G-CC-CTATC",
            scores,
        );
        alignment_tester_simd(
            "AAGTCGTAAAAGTGCACGT",
            "TAAGCCGTTAAGTGCGCGTG",
            "AAGTCGTAAAAGTGCACGT",
            "AAGCCGT-TAAGTGCGCGT",
            scores,
        );
        alignment_tester_simd("AAGTCGTAAAAGTGCACGT",
                 "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzTAAGCCGTTAAGTGCGCGTG",
                 "AAGTCGTAAAAGTGCACGT", "AAGCCGT-TAAGTGCGCGT", scores);
    }

    use test::Bencher;

    #[bench]
    fn bench_simd(b: &mut Bencher) {
        let query: Vec<char> = std::iter::repeat('x')
            .take(150)
            .chain("abc".chars())
            .chain(std::iter::repeat('x'))
            .take(330)
            .collect();
        let target: Vec<char> = std::iter::repeat('z')
            .take(2000)
            .chain("ac".chars())
            .chain(std::iter::repeat('z'))
            .take(10000)
            .collect();

        let scores = AlignmentScores {
            gap: -2,
            r#match: 3,
            miss: -3,
        };

        b.iter(|| find_alignment_simd::<LANES>(&query, &target, scores));
    }
}
