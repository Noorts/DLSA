package smithwaterman

import "container/heap"

type Score struct {
	score int
	index int
}

// An scoreArray is a min-heap of ints mapped to indices. based on https://go.dev/src/container/heap/example_intheap_test.go
type scoreArray []Score

func (h scoreArray) Len() int           { return len(h) }
func (h scoreArray) Less(i, j int) bool { return h[i].score < h[j].score }
func (h scoreArray) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *scoreArray) Push(x any) {
	// Push and Pop use pointer receivers because they modify the slice's length,
	// not just its contents.
	*h = append(*h, x.(Score))
}

func (h *scoreArray) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}

type ScoreHeap struct {
	size int
	arr  *scoreArray
}

func CreateScoreHeap(size int) ScoreHeap {
	tmp := scoreArray(make([]Score, size))
	scoreHeap := ScoreHeap{size, &tmp}
	heap.Init(scoreHeap.arr)
	return scoreHeap
}

func (h ScoreHeap) Push(index, score int) {
	heap.Pop(h.arr)
	heap.Push(h.arr, Score{index: index, score: score})
}

func (h ScoreHeap) LowestScore() int {
	return (*h.arr)[0].score
}

func (h ScoreHeap) AllScores() []Score {
	return *h.arr
}

type AlignmentResult struct {
	Score         int
	Query, Target string
}
