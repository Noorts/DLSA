package smithwaterman

import (
	"fmt"
)

func smithwaterman() {
	fmt.Println("Hello from Smith Waterman")
}

/*
*

	A one-to-one simple implementation of the Smith Waterman 2D array construction
	Assumptions
	 - Single gap penalty
*/
func FindStringScore(query string, target string) []int {
	score := make([]int, (len(query)+1)*(len(target)+1))

	substitution_score := 3
	gap_penalty := 2

	width := len(target) + 1
	height := len(query) + 1

	for y := 1; y < height; y++ {
		for x := 1; x < width; x++ {
			sub_score := substitution_score

			if query[y-1] != target[x-1] {
				sub_score = -substitution_score
			}

			score[index(x, y, width)] = max(
				max(
					0,
					score[index(x-1, y-1, width)]+sub_score,
				),
				max(
					score[index(x-1, y, width)]-gap_penalty,
					score[index(x, y-1, width)]-gap_penalty,
				),
			)
		}
	}

	return score
}

func index(x, y, width int) int {
	return x + y*width
}

func max(a, b int) int {
	if a > b {
		return a
	} else {
		return b
	}
}
