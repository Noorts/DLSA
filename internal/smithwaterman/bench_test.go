package smithwaterman

import (
	"time"
    "testing"
)

// Kinda, annoying to test, I'll just make sure it runs
func TestBenchmark(t *testing.T) {
    Benchmark(time.Duration(1e7), 4, 2)
}
