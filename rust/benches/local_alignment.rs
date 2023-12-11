extern crate criterion;
use std::time::Duration;

use self::criterion::*;
use criterion::{criterion_group, criterion_main, Criterion};
use sw::{algorithm::AlignmentScores, find_alignment_simd};

const LANES: usize = 64;
fn bench_local_alignment(c: &mut Criterion) {
    let scores = AlignmentScores {
        gap: -2,
        r#match: 3,
        miss: -3,
    };

    for query_len in (1..=6).map(|x| x * LANES) {
        let mut group = c.benchmark_group(format!("Query len: {query_len}"));

        group.warm_up_time(Duration::from_millis(300));
        group.measurement_time(Duration::from_secs(1));
        group.sample_size(100);
        for target_len in (10..=20).map(|x| 2_usize.pow(x)) {
            let query: Vec<char> = std::iter::repeat('a').take(query_len).collect();
            let target: Vec<char> = std::iter::repeat('b').take(target_len).collect();

            group.throughput(Throughput::Elements((query.len() * target.len()) as u64));

            group.bench_with_input(
                BenchmarkId::new("SIMD", target_len),
                &(&query, &target),
                |b, (ref query, ref target)| {
                    b.iter(|| find_alignment_simd::<64>(&query, &target, scores));
                },
            );
        }
        group.finish();
    }
}

criterion_group!(benches, bench_local_alignment);

criterion_main!(benches);
