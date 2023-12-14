use rand::Rng;
use sw::{
    algorithm::{find_alignment_simd_lowmem, AlignmentScores},
    find_alignment_simd,
};

#[allow(unused_imports)]
use sw::algorithm::{
    string_scores_parallel, string_scores_simd, string_scores_straight, traceback,
};

const LANES: usize = 64;

fn main() {
    let scores = AlignmentScores {
        gap: -2,
        r#match: 3,
        miss: -3,
    };

    let mut rng = rand::thread_rng();

    let charset = ['A', 'T', 'C', 'G'];

    for _i in 0..10000 {
        let query: Vec<_> = (0..)
            .map(|_| {
                let i: u8 = rng.gen();
                let char = charset[i as usize % charset.len()];

                char
            })
            .take(1000)
            .collect();

        let target: Vec<_> = (0..)
            .map(|_| {
                let i: u8 = rng.gen();
                let char = charset[i as usize % charset.len()];

                char
            })
            .take(1000)
            .collect();

        let lm = find_alignment_simd_lowmem::<LANES>(&query, &target, scores);
        let sd = find_alignment_simd::<LANES>(&query, &target, scores);

        assert_eq!(lm, sd);
    }
}
