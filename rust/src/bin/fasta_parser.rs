use itertools::iproduct;
use rayon::iter::{ParallelBridge, ParallelIterator};
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use sw::algorithm;

//parses a fasta file into a vector of strings
fn parse_fasta(file_path: &str) -> io::Result<Vec<Vec<char>>> {
    let file: File = File::open(file_path)?;
    let reader: BufReader<File> = BufReader::new(file);
    let mut lines: io::Lines<BufReader<File>> = reader.lines();
    let mut result: Vec<Vec<char>> = Vec::new();
    let mut current: Vec<char> = Vec::new();
    while let Some(line) = lines.next() {
        let line: String = line?;
        if line.starts_with('>') {
            if !current.is_empty() {
                result.push(current);
                current = Vec::new();
            }
        } else {
            let line_chars: Vec<char> = line.to_uppercase().chars().collect();
            current.extend(line_chars);
        }
    }
    if !current.is_empty() {
        result.push(current);
    }
    Ok(result)
}

//creats a vector of tuples of all possible combinations of query and target
fn create_target_pairs(
    file1: &str,
    file2: &str,
) -> io::Result<Vec<(Vec<char>, Vec<char>, i16, usize, usize)>> {
    let queries: Vec<Vec<char>> = parse_fasta(file1)?;
    let targets: Vec<Vec<char>> = parse_fasta(file2)?;
    let scores = algorithm::AlignmentScores {
        gap: -2,
        r#match: 3,
        miss: -3,
    };
    let pairs: Vec<(Vec<char>, Vec<char>, i16, usize, usize)> =
        iproduct!(queries.iter(), targets.iter())
            .map(|(query, target)| {
                let (q_res, t_res, score, max_x, max_y) =
                    sw::algorithm::find_alignment_simd_lowmem::<64>(query, target, scores);
                return (q_res, t_res, score, max_x, max_y);
            })
            .collect();
    // .max_by_key(|(_, _, score)| *score)
    // .expect("No pairs to align");
    Ok(pairs)
}

fn main() {
    let args: Vec<String> = std::env::args().collect::<Vec<_>>();
    let file1: &String = &args[1];
    let file2: &String = &args[2];
    if args.len() < 3 {
        eprintln!(
            "Usage: {} <path_to_first_fasta> <path_to_second_fasta>",
            args[0]
        );
        std::process::exit(1);
    }
    let mut pairs: Vec<(Vec<char>, Vec<char>, i16, usize, usize)> =
        create_target_pairs(file1, file2).expect("Could not create pairs");
    pairs.sort_by(|(_, _, score, _, _), (_, _, otherscore, _, _)| score.cmp(otherscore));
    for pair in pairs {
        println!(
            "Q: {:?}\nT: {:?}\nScore: {}",
            pair.0.into_iter().collect::<String>(),
            pair.1.into_iter().collect::<String>(),
            pair.2
        );
    }
}
