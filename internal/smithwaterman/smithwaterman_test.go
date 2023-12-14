package smithwaterman

import (
	"fmt"
	"strings"
	"testing"
)

// Global variables for now only for testing

func TestBasic(t *testing.T) {
	scores := AlignmentScore{
		MatchScore:      2,
		MismatchPenalty: 1,
		GapPenalty:      1,
	}

	test_substring("A", "A", "A", "A", scores, t)
	test_substring("HOI", "HOI", "HOI", "HOI", scores, t)
	test_substring("AAAAAAATAAAAAAAA", "CCTCCCCCCCCCCCCC", "T", "T", scores, t)
}

func TestNoMatch(t *testing.T) {
	scores := AlignmentScore{
		MatchScore:      2,
		MismatchPenalty: 1,
		GapPenalty:      1,
	}

	test_substring("A", "T", "", "", scores, t)
	test_substring("AAAA", "TTTT", "", "", scores, t)
	test_substring("ATATTTATTAAATATATTATATATTAA", "CCCCGCGGGGCGCGCGGCGCGCGCGCGCG", "", "", scores, t)
}

func TestGap(t *testing.T) {
	scores := AlignmentScore{
		MatchScore:      2,
		MismatchPenalty: 1,
		GapPenalty:      1,
	}
	test_substring("CCAA", "GATA", "A-A", "ATA", scores, t)
	test_substring("AA", "ATA", "A-A", "ATA", scores, t)
	test_substring("AA", "ATTA", "A", "A", scores, t)
	test_substring("AAAAAAAAA", "AAATTAAATTAAA", "AAA--AAA--AAA", "AAATTAAATTAAA", scores, t)

	scores = AlignmentScore{
		MatchScore:      3,
		MismatchPenalty: 1,
		GapPenalty:      1,
	}

	test_substring("AA", "ATTA", "A--A", "ATTA", scores, t)
	test_substring("ATA", "ATTA", "A-TA", "ATTA", scores, t)
}

func TestMismatch(t *testing.T) {
	scores := AlignmentScore{
		MatchScore:      2,
		MismatchPenalty: 1,
		GapPenalty:      1,
	}
	test_substring("ATA", "ACA", "ATA", "ACA", scores, t)
	scores = AlignmentScore{
		MatchScore:      5,
		MismatchPenalty: 2,
		GapPenalty:      3,
	}
	test_substring("ACAC", "ACGCTTTTACC", "ACAC", "ACGC", scores, t)
	test_substring("ACAC", "AGGCTTTTACC", "ACAC", "AC-C", scores, t)
}

func TestMultipleOptions(t *testing.T) {
	scores := AlignmentScore{
		MatchScore:      2,
		MismatchPenalty: 1,
		GapPenalty:      1,
	}
	test_substring("AA", "AATAA", "AA", "AA", scores, t)
	test_substring("ATTA", "ATAA", "ATTA", "AT-A", scores, t)
}

func TestAdvanced(t *testing.T) {
	scores := AlignmentScore{
		MatchScore:      2,
		MismatchPenalty: 1,
		GapPenalty:      1,
	}
	test_substring("TACGGGCCCGCTAC", "TAGCCCTATCGGTCA", "TACGGGCCCGCTA-C", "TA---G-CC-CTATC", scores, t)
	test_substring("AAGTCGTAAAAGTGCACGT", "TAAGCCGTTAAGTGCGCGTG", "AAGTCGTAAAAGTGCACGT", "AAGCCGT-TAAGTGCGCGT", scores, t)
	test_substring("AAGTCGTAAAAGTGCACGT", "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzTAAGCCGTTAAGTGCGCGTG", "AAGTCGTAAAAGTGCACGT", "AAGCCGT-TAAGTGCGCGT", scores, t)
}

func test_substring(query, target, expected_query, expected_target string, scores AlignmentScore, t *testing.T) {
	found_query, found_target, score := FindLocalAlignment(query, target, scores)
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

	if found_query != expected_query {
		t.Errorf("Did not find correct substring")
		t.Logf("Target\nFound: %s\nExpected: %s", found_target, expected_target)
		match = false
	}

	if match {
		t.Logf("Correctly found the substring for query: %s and target %s", query, target)
	} else {
		t.Errorf("Did not find the substring for query: %s and target %s", query, target)
	}
}

func formatMatrix(matrix []int, query, target string) *string {
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

	ret := output.String()

	return &ret
}
