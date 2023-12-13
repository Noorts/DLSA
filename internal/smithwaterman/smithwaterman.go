package smithwaterman

/*
#cgo LDFLAGS: ./rust/target/release/libsw.a -ldl
#include "./../../rust/header/sw.h"
*/
import "C"

import (
	"strings"
)

//Commented out for now
// var GAP_PENALTY = 1
// var MATCH_SCORE = 2
// var MISMATCH_PENALTY = 1

func findStringScore(query string, target string, matchScore int, gapPen int, mismatchPen int) []int {
	score := make([]int, (len(query)+1)*(len(target)+1))

	width := len(target) + 1
	height := len(query) + 1

	for y := 1; y < height; y++ {
		for x := 1; x < width; x++ {
			subScore := matchScore

			if query[y-1] != target[x-1] {
				subScore = -mismatchPen
			}

			score[index(x, y, width)] = max(0,
				score[index(x-1, y-1, width)]+subScore,
				score[index(x-1, y, width)]-gapPen,
				score[index(x, y-1, width)]-gapPen)
		}
	}

	return score
}

func FindLocalAlignment(query, target string, matchScore int, gapPen int, mismatchPen int) (string, string, int) {
	score := findStringScore(query, target, matchScore, gapPen, mismatchPen)

	maxIndex := 0
	maxScore := 0

	for i := 0; i < len(score); i++ {
		currentScore := score[i]
		if currentScore > maxScore {
			maxScore = currentScore
			maxIndex = i
		}
	}

	width := len(target) + 1
	x, y := index2coord(maxIndex, width)

	var queryResult, targetResult strings.Builder
	traceback(score, query, target, x, y, width, &queryResult, &targetResult, matchScore, gapPen, mismatchPen)

	return queryResult.String(), targetResult.String(), maxScore
}

func traceback(matrix []int, query, target string, x, y, width int, queryResult, targetResult *strings.Builder, matchScore int, gapPen int, mismatchPen int) {
	if x == 0 || y == 0 {
		return
	}

	if query[x-1] != target[y-1] {
		matchScore = -mismatchPen
	}

	// TODO: Evaluate what is more important in the case of multiple paths
	score := matrix[index(y, x, width)]
	if score == 0 {
		return
	} else if score == matrix[index(y-1, x-1, width)]+matchScore {
		traceback(matrix, query, target, x-1, y-1, width, queryResult, targetResult, matchScore, gapPen, mismatchPen)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteByte(target[y-1])
	} else if score == matrix[index(y, x-1, width)]-gapPen {
		traceback(matrix, query, target, x-1, y, width, queryResult, targetResult, matchScore, gapPen, mismatchPen)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteRune('-')
	} else {
		traceback(matrix, query, target, x, y-1, width, queryResult, targetResult, matchScore, gapPen, mismatchPen)
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
