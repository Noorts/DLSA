package smithwaterman

/*
#cgo LDFLAGS: ./rust/target/release/libsw.a -ldl
#include "./../../rust/header/sw.h"
*/
import "C"

import (
	"strings"
)

type AlignmentScore struct {
	MatchScore      int
	MismatchPenalty int
	GapPenalty      int
}

func findStringScore(query string, target string, scores AlignmentScore) []int {
	width := len(query) + 1
	height := len(target) + 1
	score := make([]int, width*height)

	for y := 1; y < height; y++ {
		for x := 1; x < width; x++ {
			subScore := scores.MatchScore

			if query[x-1] != target[y-1] {
				subScore = -scores.MismatchPenalty
			}

			score[index(x, y, width)] = max(0,
				score[index(x-1, y-1, width)]+subScore,
				score[index(x-1, y, width)]-scores.GapPenalty,
				score[index(x, y-1, width)]-scores.GapPenalty)
		}
	}

	return score
}

func FindLocalAlignment(query, target string, scores AlignmentScore) (string, string, int) {
	score := findStringScore(query, target, scores)

	maxIndex := 0
	maxScore := 0

	for i := 0; i < len(score); i++ {
		currentScore := score[i]
		if currentScore > maxScore {
			maxScore = currentScore
			maxIndex = i
		}
	}

	width := len(query) + 1
	x, y := index2coord(maxIndex, width)

	var queryResult, targetResult strings.Builder
	traceback(score, query, target, x, y, width, &queryResult, &targetResult, scores)

	return queryResult.String(), targetResult.String(), maxScore
}

func traceback(matrix []int, query, target string, x, y, width int, queryResult, targetResult *strings.Builder, scores AlignmentScore) {
	if x == 0 || y == 0 {
		return
	}

	matchScore := scores.MatchScore
	if query[x-1] != target[y-1] {
		matchScore = -scores.MismatchPenalty
	}

	// TODO: Evaluate what is more important in the case of multiple paths
	score := matrix[index(x, y, width)]
	if score == 0 {
		return
	} else if score == matrix[index(x-1, y-1, width)]+matchScore {
		traceback(matrix, query, target, x-1, y-1, width, queryResult, targetResult, scores)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteByte(target[y-1])
	} else if score == matrix[index(x-1, y, width)]-scores.GapPenalty {
		traceback(matrix, query, target, x-1, y, width, queryResult, targetResult, scores)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteRune('-')
	} else {
		traceback(matrix, query, target, x, y-1, width, queryResult, targetResult, scores)
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
