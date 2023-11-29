package smithwaterman

import (
	"strings"
)

var GAP_PENALTY = 1
var MATCH_SCORE = 2
var MISMATCH_PENALTY = 1

/**
 * A one-to-one simple implementation of the Smith Waterman 2D array construction
 * Assumptions
 *	 - Single gap penalty
 */
func sequentialFindStringScore(query string, target string) []int {
	score := make([]int, (len(query)+1)*(len(target)+1))

	height := len(target) + 1
	width := len(query) + 1

	for y := 1; y < height; y++ {
		for x := 1; x < width; x++ {
			sub_score := MATCH_SCORE

			if query[x-1] != target[y-1] {
				sub_score = -MISMATCH_PENALTY
			}

			score[index(x, y, width)] = max(0,
				score[index(x-1, y-1, width)]+sub_score,
				score[index(x-1, y, width)]-GAP_PENALTY,
				score[index(x, y-1, width)]-GAP_PENALTY)
		}
	}

	return score
}

func findStringScore(query string, target string) []int {
	score := make([]int, (len(query)+1)*(len(target)+1))

	height := len(target) + 1
	width := len(query) + 1

	var y int

	// return sequentialFindStringScore(query, target)
	// Has no parallel computation in this implementation
	if width >= height {
		return sequentialFindStringScore(query, target)
	}

	// First we compute the upper left triangle
	for y = 1; y < width; y++ {
		for x := 1; x <= y; x++ {
			sub_score := MATCH_SCORE

			if query[x-1] != target[y-1] {
				sub_score = -MISMATCH_PENALTY
			}

			score[index(x, y, width)] = max(0,
				score[index(x-1, y-1, width)]+sub_score,
				score[index(x-1, y, width)]-GAP_PENALTY,
				score[index(x, y-1, width)]-GAP_PENALTY,
			)
		}
	}

	// ly is the y coordinate of the left column
	// This structure is x independent. So all x can be solved in parallel as
	// long as ly is the same
	for ly := y; ly < height; ly++ {
		for x := 1; x < width; x++ {
			// We shadow y with the column dependent y coordinate that is
			// actually used by the SW-algorithm
			y := ly - (x - 1)

			sub_score := MATCH_SCORE

			if query[x-1] != target[y-1] {
				sub_score = -MISMATCH_PENALTY
			}

			score[index(x, y, width)] = max(0,
				score[index(x-1, y-1, width)]+sub_score,
				score[index(x-1, y, width)]-GAP_PENALTY,
				score[index(x, y-1, width)]-GAP_PENALTY,
			)
		}
	}

	// TODO: Actually compute the lower right triangle without recomputation
	// Right now we compute the last `width` rows this is easier to implement,
	// but computes 2x to many values
	for y := height - width; y < height; y++ {
		// for x := height - width + y < x++ {
		for x := 1; x < width; x++ {
			sub_score := MATCH_SCORE

			if query[x-1] != target[y-1] {
				sub_score = -MISMATCH_PENALTY
			}

			score[index(x, y, width)] = max(0,
				score[index(x-1, y-1, width)]+sub_score,
				score[index(x-1, y, width)]-GAP_PENALTY,
				score[index(x, y-1, width)]-GAP_PENALTY,
			)
		}
	}

	return score
}

func FindLocalAlignment(query, target string) (string, string, int) {
	score := findStringScore(query, target)

	max_index := 0
	max_score := 0

	for i := 0; i < len(score); i++ {
		current_score := score[i]
		if current_score > max_score {
			max_score = current_score
			max_index = i
		}
	}

	width := len(query) + 1
	x, y := index2coord(max_index, width)

	var queryResult, targetResult strings.Builder
	traceback(score, query, target, x, y, width, &queryResult, &targetResult)

	return queryResult.String(), targetResult.String(), max_score
}

func traceback(matrix []int, query, target string, x, y, width int, queryResult, targetResult *strings.Builder) {
	if x == 0 || y == 0 {
		return
	}

	matchScore := MATCH_SCORE
	if query[x-1] != target[y-1] {
		matchScore = -MISMATCH_PENALTY
	}

	// TODO: Evaluate what is more important in the case of multiple paths
	score := matrix[index(x, y, width)]
	if score == 0 {
		return
	} else if score == matrix[index(x-1, y-1, width)]+matchScore {
		traceback(matrix, query, target, x-1, y-1, width, queryResult, targetResult)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteByte(target[y-1])
	} else if score == matrix[index(x-1, y, width)]-GAP_PENALTY {
		traceback(matrix, query, target, x-1, y, width, queryResult, targetResult)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteRune('-')
	} else {
		traceback(matrix, query, target, x, y-1, width, queryResult, targetResult)
		queryResult.WriteRune('-')
		targetResult.WriteByte(target[y-1])
	}
}

func index(x, y, width int) int {
	return x + y*width
}

func index2coord(index, width int) (int, int) {
	return index % width, index / width
}
