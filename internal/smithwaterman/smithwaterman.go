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

			score[coord2index(x, y, width)] = max(0,
				score[coord2index(x-1, y-1, width)]+sub_score,
				score[coord2index(x-1, y, width)]-GAP_PENALTY,
				score[coord2index(x, y-1, width)]-GAP_PENALTY)
		}
	}

	return score
}

func FindLocalAlignment(query, target string, topAmount int) []AlignmentResult {
	scoreMatrix := findStringScore(query, target)

	maxScores := CreateScoreHeap(topAmount)
	for index, score := range scoreMatrix {
		if score > maxScores.LowestScore() {
			maxScores.Push(index, score)
		}
	}

	var result []AlignmentResult

	width := len(target) + 1
	for _, score := range maxScores.AllScores() {
		x, y := index2coord(score.index, width)
		var queryResult, targetResult strings.Builder
		traceback(scoreMatrix, query, target, x, y, width, &queryResult, &targetResult)
		result = append(result, AlignmentResult{score.score, queryResult.String(), targetResult.String()})
	}

	return result
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
	score := matrix[coord2index(y, x, width)]
	if score == 0 {
		return
	} else if score == matrix[coord2index(y-1, x-1, width)]+matchScore {
		traceback(matrix, query, target, x-1, y-1, width, queryResult, targetResult)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteByte(target[y-1])
	} else if score == matrix[coord2index(y, x-1, width)]-GAP_PENALTY {
		traceback(matrix, query, target, x-1, y, width, queryResult, targetResult)
		queryResult.WriteByte(query[x-1])
		targetResult.WriteRune('-')
	} else {
		traceback(matrix, query, target, x, y-1, width, queryResult, targetResult)
		queryResult.WriteRune('-')
		targetResult.WriteByte(target[y-1])
	}
}

func coord2index(x, y, width int) int {
	return x + y*width
}

func index2coord(index, width int) (int, int) {
	return index / width, index % width
}
