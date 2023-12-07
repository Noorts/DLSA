package smithwaterman

import (
	"strings"
	"time"
)

func runOnce(nQ, nT int) (time.Duration, float32) {
	const MatchScore = 1
	const GapPenalty = 2
	const MismatchPenalty = 1

	query := strings.Repeat("A", nQ)
	target := strings.Repeat("T", nT)

	start := time.Now()
	findStringScore(query, target, MatchScore, GapPenalty, MismatchPenalty)
	end := time.Now()

	elapsed := end.Sub(start)

	cups := float32(nQ*nT) / float32(elapsed.Nanoseconds()) * 1e9

	// fmt.Printf("Query: %d; target: %d, Took: %s, MCUPS: %f\n", n_q, n_t, elapsed, cups / 1e6)

	return elapsed, cups
}

func Benchmark(threshold time.Duration, qSteps, tSteps int) float32 {
	var nQ = 1 << 14
	var nT = 1 << 14

	for {
		elapsed, _ := runOnce(nQ, nT)

		if elapsed > threshold {
			break
		}

		nT *= 2
	}

	// The -2 is because the shifts in the next loops are 0-based
	nT /= 1 << (qSteps + tSteps - 2)

	var sum float32 = 0

	for iT := 0; iT < tSteps; iT++ {
		for iQ := 0; iQ < qSteps; iQ++ {
			_, cups := runOnce(nQ<<iQ, nT<<iT)
			sum += cups
		}
	}

	mean := sum / float32(qSteps*tSteps)

	return mean

}
