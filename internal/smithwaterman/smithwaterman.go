package smithwaterman

import (
	"strings"
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

			score[index(x, y, width)] = max(0,
				score[index(x-1, y-1, width)]+sub_score,
				score[index(x-1, y, width)]-GAP_PENALTY,
				score[index(x, y-1, width)]-GAP_PENALTY)
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

	width := len(target) + 1
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
	score := matrix[index(y, x, width)]
	if score == 0 {
		return
	} else if score == matrix[index(y-1, x-1, width)]+matchScore {
		traceback(matrix, query, target, x-1, y-1, width, queryResult, targetResult)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteByte(target[y-1])
	} else if score == matrix[index(y, x-1, width)]-GAP_PENALTY {
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
	return index / width, index % width
}

// Low mem variants
func FindLocalAlignmentLowMem(query, target string) (string, string, int) {
	width := len(query) + 1
	height := len(target) + 1
	wrapping_height := len(query) * (1 + (MATCH_SCORE / GAP_PENALTY))

	score := make([]int, width*wrapping_height)

	best_query_result := ""
	best_target_result := ""

	max_score := 0

	for y := 1; y < height; y++ {
		for x := 1; x < width; x++ {
			sub_score := MATCH_SCORE

			if query[x-1] != target[y-1] {
				sub_score = -MISMATCH_PENALTY
			}

			new_score := max(0,
				score[index_wrapping(x-1, y-1, width, wrapping_height)]+sub_score,
				score[index_wrapping(x-1, y, width, wrapping_height)]-GAP_PENALTY,
				score[index_wrapping(x, y-1, width, wrapping_height)]-GAP_PENALTY)

			score[index_wrapping(x, y, width, wrapping_height)] = new_score

			if max_score < new_score {
				max_score = new_score
				var queryResult, targetResult strings.Builder
				traceback_wrapping(score, query, target, x, y, width, wrapping_height, &queryResult, &targetResult)
				best_query_result = queryResult.String()
				best_target_result = targetResult.String()
			}
		}
	}

	return best_query_result, best_target_result, max_score
}

func index_wrapping(x, y, width, wrapping_height int) int {
	return x + (y%wrapping_height)*width
}

func traceback_wrapping(matrix []int, query, target string, x, y, width, wrapping_height int, queryResult, targetResult *strings.Builder) {
	if x == 0 || y == 0 {
		return
	}

	matchScore := MATCH_SCORE
	if query[x-1] != target[y-1] {
		matchScore = -MISMATCH_PENALTY
	}

	// TODO: Evaluate what is more important in the case of multiple paths
	score := matrix[index_wrapping(x, y, width, wrapping_height)]
	if score == 0 {
		return
	} else if score == matrix[index_wrapping(x-1, y-1, width, wrapping_height)]+matchScore {
		traceback_wrapping(matrix, query, target, x-1, y-1, width, wrapping_height, queryResult, targetResult)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteByte(target[y-1])
	} else if score == matrix[index_wrapping(x-1, y, width, wrapping_height)]-GAP_PENALTY {
		traceback_wrapping(matrix, query, target, x-1, y, width, wrapping_height, queryResult, targetResult)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteRune('-')
	} else {
		traceback_wrapping(matrix, query, target, x, y-1, width, wrapping_height, queryResult, targetResult)
		queryResult.WriteRune('-')
		targetResult.WriteByte(target[y-1])
	}
}
