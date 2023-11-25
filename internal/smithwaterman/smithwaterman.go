package smithwaterman

import (
	"bytes"
	"fmt"
)

var GAP_PENALTY = 1
var MATCH_SCORE = 2
var MISMATCH_PENALTY = 1

/*
*

	A one-to-one simple implementation of the Smith Waterman 2D array construction
	Assumptions
	 - Single gap penalty
*/

func findStringScore(query string, target string) []int {
	score := make([]int, (len(query)+1)*(len(target)+1))

	width := len(target) + 1
	height := len(query) + 1

	for y := 1; y < height; y++ {
		for x := 1; x < width; x++ {
			sub_score := MATCH_SCORE

			if query[y-1] != target[x-1] {
				sub_score = -MISMATCH_PENALTY
			}

			score[index(x, y, width)] = max(
				max(0, score[index(x-1, y-1, width)]+sub_score),
				max(
					score[index(x-1, y, width)]-GAP_PENALTY,
					score[index(x, y-1, width)]-GAP_PENALTY,
				),
			)
		}
	}

	return score
}

func findLocalAlignment(query, target string) (string, string) {
	score := findStringScore(query, target)

	max_index := 0
	max_score := 0

	width := len(target) + 1
	// height := len(query) + 1

	for i := 0; i < len(score); i++ {
		current_score := score[i]
		if current_score > max_score {
			max_score = current_score
			max_index = i
		}
	}

	var current_score = score[max_index]
	current_index := max_index

	var query_result bytes.Buffer
	var target_result bytes.Buffer

	x, y := index2coord(current_index, width)
	x -= 1
	y -= 1

	for current_score > 0 {
		// If we move up we skip a value in the target string
		// If we move left we skip a value in the query string
		next := score[current_index-1-width]
		left := score[current_index-1]
		up := score[current_index-width]

		// fmt.Printf("Visiting index: %d; Coord: %d, %d\n", current_index, x, y)

		if next >= max(left, up) {
			// fmt.Printf("Indexing string '%s' at index: %d", query, x)
			query_result.WriteByte(query[y])
			target_result.WriteByte(target[x])
			current_index -= width + 1
			x -= 1
			y -= 1
			// TODO: Evaluate what is more important in the case of equivalence
		} else if left > up {
			// query_result.WriteByte(query[x])
			query_result.WriteRune('-')
			current_index -= 1
			x -= 1
		} else {
			target_result.WriteRune('-')
			current_index -= width
			y -= 1
		}

		current_score = score[current_index]
	}

	fmt.Printf("Remaining x: %d, y: %d\n", x, y)

	for i := -1; i < x; i++ {
		target_result.WriteRune('-')
	}

	for i := -1; i < y; i++ {
		query_result.WriteRune('-')
	}

	return string_rev(query_result.String()), string_rev(target_result.String())
}

func string_rev(inp string) string {
	runes := []rune(inp)

	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}

	return string(runes)
}

func index(x, y, width int) int {
	return x + y*width
}

func index2coord(index, width int) (int, int) {
	return index % width, index / width
}
