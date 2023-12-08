package smithwaterman

import (
	"fmt"
	"runtime"
	"strings"
	"testing"
)

func TestIndex(t *testing.T) {
	width := 7
	for i := 0; i < 10000; i++ {
		x, y := index2coord(i, width)
		i_new := index(x, y, width)

		if i_new != i {
			t.Fatalf("Failed index %d", i)
		}
	}
}

func TestBasic(t *testing.T) {
	test_substring("A", "A", "A", "A", t)
	test_substring("HOI", "HOI", "HOI", "HOI", t)
	test_substring("AAAAAAATAAAAAAAA", "CCTCCCCCCCCCCCCC", "T", "T", t)
}

func TestNoMatch(t *testing.T) {
	test_substring("A", "T", "", "", t)
	test_substring("AAAA", "TTTT", "", "", t)
	test_substring("ATATTTATTAAATATATTATATATTAA", "CCCCGCGGGGCGCGCGGCGCGCGCGCGCG", "", "", t)
}

func TestGap(t *testing.T) {
	test_with_scoring(1, 1, 2, "CCAA", "GATA", "A-A", "ATA", t)
	test_with_scoring(1, 1, 2, "AA", "ATA", "A-A", "ATA", t)
	test_with_scoring(1, 1, 2, "AA", "ATTA", "A", "A", t)
	test_with_scoring(1, 1, 3, "AA", "ATTA", "A--A", "ATTA", t)
	test_with_scoring(1, 1, 3, "ATA", "ATTA", "A-TA", "ATTA", t)
	test_with_scoring(1, 1, 2, "AAAAAAAAA", "AAATTAAATTAAA", "AAA--AAA--AAA", "AAATTAAATTAAA", t)
}

func TestMismatch(t *testing.T) {
	test_with_scoring(1, 1, 2, "ATA", "ACA", "ATA", "ACA", t)
	test_with_scoring(3, 2, 5, "ACAC", "ACGCTTTTACC", "ACAC", "ACGC", t)
	test_with_scoring(3, 2, 5, "ACAC", "AGGCTTTTACC", "ACAC", "AC-C", t)
}

func TestMultipleOptions(t *testing.T) {
	test_with_scoring(1, 1, 2, "AA", "AATAA", "AA", "AA", t)
	test_with_scoring(1, 1, 2, "ATTA", "ATAA", "ATTA", "A-TA", t)
}

func TestAdvanced(t *testing.T) {
	test_with_scoring(1, 1, 2, "TACGGGCCCGCTAC", "TAGCCCTATCGGTCA", "TACGGGCCCGCTA-C", "TA---G-CC-CTATC", t)
	test_with_scoring(1, 1, 2, "AAGTCGTAAAAGTGCACGT", "TAAGCCGTTAAGTGCGCGTG", "AAGTCGTAAAAGTGCACGT", "AAGCCGT-TAAGTGCGCGT", t)
}

func TestParallel(t *testing.T) {
	test_with_scoring(1, 1, 2, "TACGGGCCCGCTAC", "zzzzzzzzzzzzzzzzzzzzzzTAGCCCTATCGGTCAzzzzzzzzzzzzzzzzzzzz", "TACGGGCCCGCTA-C", "TA---G-CC-CTATC", t)
	test_with_scoring(1, 1, 2, "AAGTCGTAAAAGTGCACGT", "TAAGCCGTTAAGTGCGCGTG", "AAGTCGTAAAAGTGCACGT", "AAGCCGT-TAAGTGCGCGT", t)
}

func test_with_scoring(gap int, mismatch int, match int, query, target, expected_query, expected_target string, t *testing.T) {
	if gap < 0 || mismatch < 0 || match < 0 {
		t.Log("Normally these should be all positive")
	}
	oldGap := GAP_PENALTY
	oldMismatch := MISMATCH_PENALTY
	oldMatch := MATCH_SCORE
	GAP_PENALTY = gap
	MISMATCH_PENALTY = mismatch
	MATCH_SCORE = match

	test_substring(query, target, expected_query, expected_target, t)

	GAP_PENALTY = oldGap
	MISMATCH_PENALTY = oldMismatch
	MATCH_SCORE = oldMatch
}

func test_substring(query, target, expected_query, expected_target string, t *testing.T) {
	found_query, found_target, score := FindLocalAlignment(query, target)
	if score == 0 {
		t.Logf("Found no substring")
		return
	}
	match := true

	if found_query != expected_query {
		t.Errorf("Did not find correct substring")
		t.Logf("Query\nFound: %s\nExpected: %s", found_query, expected_query)
		match = false
	}

	if found_target != expected_target {
		t.Errorf("Did not find correct substring")
		t.Logf("Target\nFound: %s\nExpected: %s", found_target, expected_target)
		match = false
	}

	if match {
		t.Logf("Correctly found the substring for query: %s and target %s", query, target)
	} else {
		t.Errorf("Did not find the substring for query: %s and target %s", query, target)

		printMatrix(findStringScore(query, target), target, query)
		t.FailNow()
	}
}

func printMatrix(matrix []int, query, target string) *string {
	width := len(query) + 1
	height := len(target) + 1

	if len(matrix) != width*height {
		ret := "Matrix is not the same size as the provided width * height"
		return &ret
	}

	var output strings.Builder

	output.WriteString("       ")

	for x := 0; x < width-1; x++ {
		output.WriteString(fmt.Sprintf(" %c  ", query[x]))
	}

	output.WriteRune('\n')

	for y := 0; y < height; y++ {
		if y > 0 {
			output.WriteString(fmt.Sprintf(" %c", target[y-1]))
		} else {
			output.WriteString("  ")
		}
		for x := 0; x < width; x++ {
			output.WriteString(fmt.Sprintf("%3d ", matrix[index(x, y, width)]))
		}
		output.WriteRune('\n')
	}

	fmt.Println(output.String())

	return nil
}

const NumBenchmarks = 10

func benchmarkSequential(query, target string, b *testing.B) {
	size := len(query) * len(target)
	var _ []int
	b.ResetTimer()

	for i := 0; i < NumBenchmarks; i++ {
		b.StartTimer()
		_ = sequentialFindStringScore(query, target)
		b.StopTimer()
	}

	mcups := float64(size) / (b.Elapsed().Seconds() / NumBenchmarks) / 1_000_000
	b.Logf("Sequential for size %d: %.03f MCUPS\n", size, mcups)
}

func benchmarkParallel(query, target string, NUMPROC int, b *testing.B) {
	size := len(query) * len(target)
	var _ []int
	runtime.GOMAXPROCS(NUMPROC)
	b.ResetTimer()

	for i := 0; i < NumBenchmarks; i++ {
		b.StartTimer()
		_ = parallelFindStringScore(query, target, NUMPROC)
		b.StopTimer()
	}

	mcups := float64(size) / (b.Elapsed().Seconds() / NumBenchmarks) / 1_000_000
	b.Logf("Parallel for size %d with %d procs: %.03f MCUPS\n", size, NUMPROC, mcups)
}

func BenchmarkMatrix1k(b *testing.B) {
	query := strings.Repeat("A", 330)
	target := strings.Repeat("T", 1000)
	benchmarkSequential(query, target, b)

	benchmarkParallel(query, target, 1, b)
	benchmarkParallel(query, target, 2, b)
	benchmarkParallel(query, target, 3, b)
	benchmarkParallel(query, target, 4, b)
}

func BenchmarkMatrix10k(b *testing.B) {
	query := strings.Repeat("A", 330)
	target := strings.Repeat("T", 10000)
	benchmarkSequential(query, target, b)

	benchmarkParallel(query, target, 1, b)
	benchmarkParallel(query, target, 2, b)
	benchmarkParallel(query, target, 3, b)
	benchmarkParallel(query, target, 4, b)
}

func BenchmarkMatrix100kweak(b *testing.B) {
	N := 50
	target := strings.Repeat("T", 100000)

	for i := 1; i <= 4; i++ {
		query := strings.Repeat("A", N*i)
		benchmarkParallel(query, target, i, b)
	}
}

func BenchmarkMatrix100k(b *testing.B) {
	query := strings.Repeat("A", 330)
	target := strings.Repeat("T", 100000)
	benchmarkSequential(query, target, b)

	benchmarkParallel(query, target, 1, b)
	benchmarkParallel(query, target, 2, b)
	benchmarkParallel(query, target, 3, b)
	benchmarkParallel(query, target, 4, b)
}
