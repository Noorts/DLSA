package smithwaterman

import (
	"strings"
	"time"
)

func run_once(n_q, n_t int) (time.Duration, float32) {
	query := strings.Repeat("A", n_q)
	target := strings.Repeat("T", n_t)

	start := time.Now()
	findStringScore(query, target)
	end := time.Now()

	elapsed := end.Sub(start)

	cups := float32(n_q*n_t) / float32(elapsed.Nanoseconds()) * 1e9

	// fmt.Printf("Query: %d; target: %d, Took: %s, MCUPS: %f\n", n_q, n_t, elapsed, cups / 1e6)

	return elapsed, cups
}

func Benchmark(threshold time.Duration, q_steps int) float32 {
	var n_q int = 1 << 8
	var n_t int = 1 << 14

	for true {
		elapsed, _ := run_once(n_q, n_t)

		if elapsed > threshold {
			break
		}

		n_t *= 2
	}

	n_t /= 1 << q_steps

	var sum float32 = 0

	for i := 0; i <= q_steps; i++ {
		_, cups := run_once(n_q, n_t)
		sum += cups
		n_q *= 2
	}

	return sum / float32(q_steps)
}
