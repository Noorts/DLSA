package smithwaterman

import (
	"testing"
)

// Example as listed on Wikipedia
func TestExample1(t *testing.T) {
	matrix := findStringScore("TGTTACGG", "GGTTGACTA")

	max := 0

	for i := 0; i < len(matrix); i++ {
		if max < matrix[i] {
			max = matrix[i]
		}
	}

	if max != 13 {
		t.Errorf("Expected max value 13 found %d", max)
	} else {
		t.Logf("Test succeeded; found max: %d", max)
	}
}

func TestFindTargetSubstring(t *testing.T) {
	test_substring("A", "A", "A", "A", t)
	test_substring("HOI", "HOI", "HOI", "HOI", t)
	test_substring("HOI", "OI", "-OI", "OI", t)
	test_substring("TACGGGCCCGCTAC", "TAGCCCTATCGGTCA", "TACGGGCCCGCTA-C", "TA---G-CC-CTATC", t)
}

func test_substring(query, target, expected_query, expected_target string, t *testing.T) {
	found_query, found_target := findLocalAlignment(query, target)

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
