package worker

// #cgo LDFLAGS: ./rust/target/release/libsw.a -ldl
// #include "./../../rust/header/sw.h"
import "C"

import (
	"dlsa/internal/smithwaterman"
	"errors"
)

type Result struct {
	QueryPtr  *C.char
	TargetPtr *C.char
	Score     int
	MaxX      int
	MaxY      int
}

type GoResult struct {
	Query  string
	Target string
	Score  uint16
	MaxX   uint64
	MaxY   uint64
}

func cCharPtrToString(cStr *C.char) string {
	return C.GoString(cStr)
}

func ConvertResultToGoResult(cResult *C.struct_Result) GoResult {

	query := cCharPtrToString(cResult.query_ptr)
	target := cCharPtrToString(cResult.target_ptr)
	score := uint16(cResult.score)
	maxX := uint64(cResult.max_x)
	maxY := uint64(cResult.max_y)

	return GoResult{
		Query:  query,
		Target: target,
		Score:  score,
		MaxX:   maxX,
		MaxY:   maxY,
	}
}

// TODO: Some kind of logic to determine whether to use low mem, simd, or just sequential
// func FindRustAlignmentParallel(query, target string) GoResult {
// 	queryC := C.CString(query)
// 	targetC := C.CString(target)

// 	threads := C.ulong(4)
// 	cResult_ref := C.find_alignment_parallel(queryC, targetC, threads)
// 	goResult := convertResultToGoResult(cResult_ref)

// 	defer FreeAlignmentResult(cResult_ref)

// 	return goResult
// }

func FindRustAlignmentSequential(query, target string, alignmentScore smithwaterman.AlignmentScore) (*GoResult, error) {
	queryC := C.CString(query)
	targetC := C.CString(target)

	alignmentScoreC := C.struct_AlignmentScores{
		gap:   C.ushort(alignmentScore.GapPenalty),
		match: C.ushort(alignmentScore.MatchScore),
		miss:  C.ushort(alignmentScore.MismatchPenalty),
	}

	cResult_ref := C.find_alignment_sequential_straight(queryC, targetC, alignmentScoreC)
	if cResult_ref == nil {
		return nil, errors.New("Crash in rust sequential alignment")
	}
	goResult := convertResultToGoResult(cResult_ref)

	defer FreeAlignmentResult(cResult_ref)

	return &goResult, nil
}

func FindRustAlignmentSimd(query, target string, alignmentScore smithwaterman.AlignmentScore) (*GoResult, error) {
	queryC := C.CString(query)
	targetC := C.CString(target)
	alignmentScoreC := C.struct_AlignmentScores{
		gap:   C.ushort(alignmentScore.GapPenalty),
		match: C.ushort(alignmentScore.MatchScore),
		miss:  C.ushort(alignmentScore.MismatchPenalty),
	}

	cResult := C.find_alignment_simd(queryC, targetC, alignmentScoreC)
	if cResult == nil {
		return nil, errors.New("Crash in rust SIMD alignment")
	}

	goResult := convertResultToGoResult(cResult)

	defer FreeAlignmentResult(cResult)

	return &goResult, nil
}

func FindRustAlignmentSimdLowMem(query, target string, alignmentScore smithwaterman.AlignmentScore) (*GoResult, error) {
	queryC := C.CString(query)
	targetC := C.CString(target)
	alignmentScoreC := C.struct_AlignmentScores{
		gap:   C.ushort(alignmentScore.GapPenalty),
		match: C.ushort(alignmentScore.MatchScore),
		miss:  C.ushort(alignmentScore.MismatchPenalty),
	}

	cResult := C.find_alignment_low_memory(queryC, targetC, alignmentScoreC)
	if cResult == nil {
		return nil, errors.New("Crash in SIMD ringbuffer alignment")
	}

	goResult := convertResultToGoResult(cResult)

	defer FreeAlignmentResult(cResult)

	return &goResult, nil
}

func cCharPtrToGoString(cStr *C.char) string {
	return C.GoString(cStr)
}

// TODO: Length and score
func convertResultToGoResult(cResult *C.struct_Result) GoResult {
	return GoResult{
		Query:  cCharPtrToGoString(cResult.query_ptr),
		Target: cCharPtrToGoString(cResult.target_ptr),
		Score:  uint16(cResult.score),
		MaxX:   uint64(cResult.max_x),
		MaxY:   uint64(cResult.max_y),
	}
}

// TODO: This should free the C strings
func FreeAlignmentResult(cResult *C.struct_Result) {
	C.free_alignment_result(cResult)
}

// TODO: Ask someone, is this neccassary?
func FreeCString(cStr *C.char) {
	C.free_c_string(cStr)
}
