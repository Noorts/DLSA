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

func Benchmark(threshold time.Duration, q_steps, t_steps int) float32 {
	var n_q int = 1 << 14
	var n_t int = 1 << 14

	for true {
		elapsed, _ := run_once(n_q, n_t)

		if elapsed > threshold {
			break
		}

		n_t *= 2
	}

	// The -2 is because the shifts in the next loops are 0-based
	n_t /= 1 << (q_steps + t_steps - 2)

	var sum float32 = 0

	for i_t := 0; i_t < t_steps; i_t++ {
		for i_q := 0; i_q < q_steps; i_q++ {
			_, cups := run_once(n_q<<i_q, n_t<<i_t)
			sum += cups
		}
	}

	mean := sum / float32(q_steps*t_steps)

	return mean

}
