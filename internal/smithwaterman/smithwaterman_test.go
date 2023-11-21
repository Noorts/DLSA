package smithwaterman

import (
	"testing"
)

// Example as listed on Wikipedia
func TestExample1(t *testing.T) {
	matrix := FindStringScore("TGTTACGG", "GGTTGACTA")

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
