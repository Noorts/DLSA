extern crate criterion;
use std::time::Duration;

use self::criterion::*;
use criterion::{criterion_group, criterion_main, Criterion};
use sw::{
    algorithm::{find_alignment_simd_lowmem, AlignmentScores},
    find_alignment_sequential, find_alignment_sequential_straight, find_alignment_simd,
};

const LANES: usize = 64;

fn benchmark_lane_count_simd(c: &mut Criterion) {
    let scores = AlignmentScores {
        gap: -2,
        r#match: 3,
        miss: -3,
    };

    // Closest value to our competition
    let query_len = 5 * LANES;

    let mut group = c.benchmark_group(format!("SIMD ringbuffer lane count"));

    group.warm_up_time(Duration::from_millis(300));
    group.measurement_time(Duration::from_secs(2));
    group.sample_size(100);
    let query: Vec<char> = std::iter::repeat('a').take(query_len).collect();

    for target_len in (3..=6).map(|x| 10_usize.pow(x)) {
        let target_disjoint: Vec<char> = std::iter::repeat('b').take(target_len).collect();
        group.throughput(Throughput::Elements((query_len * target_len) as u64));
        group.bench_with_input(
            BenchmarkId::new("01 lanes", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<1>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("02 lanes", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<2>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("04 lanes", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<4>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("08 lanes", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<8>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("16 lanes", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<16>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("32 lanes", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<32>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("64 lanes", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<64>(&query, &target, scores));
            },
        );
    }
    group.finish();
}

fn benchmark_equal_disjoint(c: &mut Criterion) {
    let scores = AlignmentScores {
        gap: -2,
        r#match: 3,
        miss: -3,
    };

    let mut group = c.benchmark_group(format!("Equal vs disjoint (SIMD / SIMD + Ringbuffer)"));

    // Closest value to our competition
    let query_len = 5 * LANES;

    group.warm_up_time(Duration::from_millis(300));
    group.measurement_time(Duration::from_secs(2));
    group.sample_size(100);
    for target_len in (3..=6).map(|x| 10_usize.pow(x)) {
        let query: Vec<char> = std::iter::repeat('a').take(query_len).collect();
        let target_equal: Vec<char> = std::iter::repeat('b').take(target_len).collect();
        let target_disjoint: Vec<char> = std::iter::repeat('b').take(target_len).collect();

        group.throughput(Throughput::Elements((query_len * target_len) as u64));

        group.bench_with_input(
            BenchmarkId::new("SIMD (Equal)", target_len),
            &(&query, &target_equal),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<64>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("SIMD (Disjoint)", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<64>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("SIMD ringbuffer (Equal)", target_len),
            &(&query, &target_equal),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd_lowmem::<64>(&query, &target, scores));
            },
        );
        group.bench_with_input(
            BenchmarkId::new("SIMD ringbuffer (Disjoint)", target_len),
            &(&query, &target_disjoint),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd_lowmem::<64>(&query, &target, scores));
            },
        );
    }
    group.finish();
}

// criterion_group!(benches, bench_local_alignment, bench_local_alignment_random);
criterion_group!(
    benches,
    benchmark_equal_disjoint,
    benchmark_lane_count_simd,
);

criterion_main!(benches);
