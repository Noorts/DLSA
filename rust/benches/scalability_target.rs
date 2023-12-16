extern crate criterion;
use std::time::Duration;

use self::criterion::*;
use criterion::{criterion_group, criterion_main, Criterion};
use sw::{
    algorithm::{find_alignment_simd_lowmem, AlignmentScores},
    find_alignment_sequential, find_alignment_sequential_straight, find_alignment_simd,
};

const LANES: usize = 64;
fn benchmark_scalability_target(c: &mut Criterion) {
    let scores = AlignmentScores {
        gap: -2,
        r#match: 3,
        miss: -3,
    };

    let mut group = c.benchmark_group(format!("Target scalability"));

    // Closest value to our competition
    let query_len = 5 * LANES;

    group.warm_up_time(Duration::from_millis(300));
    group.measurement_time(Duration::from_secs(10));
    group.sample_size(100);
    for target_len in (3..=5).map(|x| 10_usize.pow(x)) {
        let query: Vec<char> = std::iter::repeat('a').take(query_len).collect();
        let target: Vec<char> = std::iter::repeat('b').take(target_len).collect();

        group.throughput(Throughput::Elements((query.len() * target.len()) as u64));

        group.bench_with_input(
            BenchmarkId::new("SIMD (lowmem)", target_len),
            &(&query, &target),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd_lowmem::<64>(&query, &target, scores));
            },
        );

        group.bench_with_input(
            BenchmarkId::new("SIMD", target_len),
            &(&query, &target),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_simd::<64>(&query, &target, scores));
            },
        );

        group.bench_with_input(
            BenchmarkId::new("Sequential (diagonal)", target_len),
            &(&query, &target),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_sequential(&query, &target, scores));
            },
        );

        group.bench_with_input(
            BenchmarkId::new("Sequential (straight)", target_len),
            &(&query, &target),
            |b, (ref query, ref target)| {
                b.iter(|| find_alignment_sequential_straight(&query, &target, scores));
            },
        );
    }
    group.finish();
}

criterion_group!(
    benches,
    benchmark_scalability_target,
);

criterion_main!(benches);
