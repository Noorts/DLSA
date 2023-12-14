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

type AlignResult = (Vec<char>, Vec<char>, i16);

pub fn find_alignment_sequential(
    query: &[char],
    target: &[char],
    scores: AlignmentScores,
) -> AlignResult {
    let data = string_scores_sequential(query, target, scores);
    let mut query_result = Vec::with_capacity(query.len());
    let mut target_result = Vec::with_capacity(target.len());

    let width = query.len() + 1;
    // TODO: Find max index
    let max_index = data.argmax();
    let (x, y) = coord(max_index, width);
    traceback(
        &data,
        query,
        target,
        x,
        y,
        width,
        &mut query_result,
        &mut target_result,
        scores,
    );

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

    let width = query.len() + 1;
    let (_, max_index) = data.argminmax();

    let (x, y) = coord(max_index, width);
    traceback_straight(
        &data,
        query,
        target,
        x,
        y,
        width,
        &mut query_result,
        &mut target_result,
        scores,
    );

    (query_result, target_result, 0)
}

pub fn find_alignment_parallel(
    query: &[char],
    target: &[char],
    threads: usize,
    scores: AlignmentScores,
) -> AlignResult {
    let data = string_scores_parallel(query, target, scores, threads);
    let mut query_result = Vec::with_capacity(query.len());
    let mut target_result = Vec::with_capacity(target.len());

    let width = query.len() + 1;
    if data.is_empty() {
        return (query_result, target_result, 0);
    }
    let argmax = data.argmax();
    let (x, y) = coord(argmax, width);
    traceback(
        &data,
        query,
        target,
        x,
        y,
        width,
        &mut query_result,
        &mut target_result,
        scores,
    );

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
        (index % width, index / width)
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

        number + (multiple - remainder)
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

    println!();

    for y in 1..height {
        print!(" {} ", target[y - 1]);
        for x in 1..width {
            print!(" {:3} ", data[index(x, y, width)]);
        }
        println!();
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

    println!();

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
        println!();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{algorithm::find_alignment_simd_lowmem, utils::*};

    const LANES: usize = 64;

    const SCORES: AlignmentScores = AlignmentScores {
        gap: -1,
        r#match: 2,
        miss: -1,
    };

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

    fn alignment_tester(
        alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult,
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
        let res = alignment_function(&q_in, &t_in, scores);
        assert_eq!(&res.0, q_out);
        assert_eq!(&res.1, t_out);
    }

    fn test_basic(alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult) {
        alignment_tester(alignment_function, "A", "A", "A", "A", SCORES);
        alignment_tester(alignment_function, "HOI", "HOI", "HOI", "HOI", SCORES);
        alignment_tester(
            alignment_function,
            "AAAAAAATAAAAAAAA",
            "CCTCCCCCCCCCCCCC",
            "T",
            "T",
            SCORES,
        );
    }

    fn test_no_match(alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult) {
        alignment_tester(alignment_function, "A", "T", "", "", SCORES);
        alignment_tester(alignment_function, "AAAA", "TTTT", "", "", SCORES);
        alignment_tester(
            alignment_function,
            "ATATTTATTAAATATATTATATATTAA",
            "CCCCGCGGGGCGCGCGGCGCGCGCGCGCG",
            "",
            "",
            SCORES,
        );
    }

    fn test_gap(alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult) {
        alignment_tester(alignment_function, "CCAA", "GATA", "A-A", "ATA", SCORES);
        alignment_tester(alignment_function, "AA", "ATA", "A-A", "ATA", SCORES);
        alignment_tester(alignment_function, "AA", "ATTA", "A", "A", SCORES);
        alignment_tester(
            alignment_function,
            "AAAAAAAAA",
            "AAATTAAATTAAA",
            "AAA--AAA--AAA",
            "AAATTAAATTAAA",
            SCORES,
        );

        let scores_alternative = AlignmentScores {
            gap: -1,
            r#match: 3,
            miss: -1,
        };

        alignment_tester(
            alignment_function,
            "AA",
            "ATTA",
            "A--A",
            "ATTA",
            scores_alternative,
        );
        alignment_tester(
            alignment_function,
            "ATA",
            "ATTA",
            "A-TA",
            "ATTA",
            scores_alternative,
        );
    }

    fn test_mismatch(alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult) {
        alignment_tester(alignment_function, "ATA", "ACA", "ATA", "ACA", SCORES);

        let scores_alternative = AlignmentScores {
            gap: -3,
            r#match: 5,
            miss: -2,
        };

        alignment_tester(
            alignment_function,
            "ACAC",
            "ACGCTTTTACC",
            "ACAC",
            "ACGC",
            scores_alternative,
        );
        alignment_tester(
            alignment_function,
            "ACAC",
            "AGGCTTTTACC",
            "ACAC",
            "AC-C",
            scores_alternative,
        );
    }

    fn test_multiple_options(
        alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult,
    ) {
        alignment_tester(alignment_function, "AA", "AATAA", "AA", "AA", SCORES);
        alignment_tester(alignment_function, "ATTA", "ATAA", "ATTA", "A-TA", SCORES);
    }

    fn test_advanced_short(
        alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult,
    ) {
        alignment_tester(
            alignment_function,
            "TACGGGCCCGCTAC",
            "TAGCCCTATCGGTCA",
            "TACGGGCCCGCTA-C",
            "TA---G-CC-CTATC",
            SCORES,
        );
        alignment_tester(
            alignment_function,
            "AAGTCGTAAAAGTGCACGT",
            "TAAGCCGTTAAGTGCGCGTG",
            "AAGTCGTAAAAGTGCACGT",
            "AAGCCGT-TAAGTGCGCGT",
            SCORES,
        );
    }

    fn test_long(alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult) {
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

        alignment_tester(alignment_function, &*query, &*target, "abc", "abc", SCORES);

        let target2 = std::iter::repeat('z')
            .take(2000)
            .chain("ac".chars())
            .chain(std::iter::repeat('z').take(1000))
            .collect::<String>();

        alignment_tester(alignment_function, &*query, &*target2, "abc", "a-c", SCORES);
    }

    fn test_all(alignment_function: fn(&[char], &[char], AlignmentScores) -> AlignResult) {
        test_basic(alignment_function);
        test_no_match(alignment_function);
        test_gap(alignment_function);
        test_mismatch(alignment_function);
        test_multiple_options(alignment_function);
        test_advanced_short(alignment_function);
        test_long(alignment_function);
    }

    // TODO: Fix algorihm
    #[test]
    fn test_all_sequential() {
        test_all(find_alignment_sequential);
    }

    #[test]
    fn test_all_sequential_straight() {
        test_all(find_alignment_sequential_straight);
    }

    // fn find_alignment_parallel_wrapper<const THREADS: usize>(
    //     query: &[char],
    //     target: &[char],
    //     scores: AlignmentScores,
    // ) -> AlignResult {
    //     return find_alignment_parallel(query, target, THREADS, scores);
    // }
    //
    // // TODO: Fix algorihm
    // #[test]
    // fn test_all_parallel() {
    //     test_all(find_alignment_parallel_wrapper::<2>);
    //     test_all(find_alignment_parallel_wrapper::<3>);
    //     test_all(find_alignment_parallel_wrapper::<4>);
    // }

    #[test]
    fn test_all_simd() {
        test_all(find_alignment_simd::<LANES>);
    }

    #[test]
    fn test_all_simd_lowmem() {
        test_all(find_alignment_simd_lowmem::<LANES>);
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
