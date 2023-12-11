package worker

// #cgo LDFLAGS: ./rust/target/release/libsw.a -ldl
// #include "./../../rust/header/sw.h"
import "C"

type Result struct {
	QueryPtr  *C.char
	TargetPtr *C.char
}

type GoResult struct {
	Query  string
	Target string
	Score  int
	Length int
}

//TODO: Some kind of logic to determine whether to use low mem, simd, or just sequential

func FindRustAlignmentParallel(query, target string) GoResult {
	queryC := C.CString(query)
	targetC := C.CString(target)

	//TODO: How many threads? Maybe doesn't matter, probably won't be using this
	threads := C.ulong(4)
	cResult := C.find_alignment_parallel(queryC, targetC, threads)

	result := convertCResultToResult(cResult)
	goResult := convertResultToGoResult(result)

	defer FreeAlignmentResult(queryC, targetC)

	return goResult
}

func FindRustAlignmentSequential(query, target string) GoResult {
	queryC := C.CString(query)
	targetC := C.CString(target)

	cResult := C.find_alignment_sequential_straight(queryC, targetC)
	result := convertCResultToResult(cResult)
	goResult := convertResultToGoResult(result)

	defer FreeAlignmentResult(queryC, targetC)

	return goResult
}

// TODO: Test if this works on Mac M1
func FindRustAlignmentSimd(query, target string) GoResult {
	queryC := C.CString(query)
	targetC := C.CString(target)

	cResult := C.find_alignment_simd(queryC, targetC)
	result := convertCResultToResult(cResult)
	goResult := convertResultToGoResult(result)

	defer FreeAlignmentResult(queryC, targetC)

	return goResult

}

func cCharPtrToGoString(cStr *C.char) string {
	return C.GoString(cStr)
}

// TODO: Length and score
func convertResultToGoResult(result Result) GoResult {
	return GoResult{
		Query:  cCharPtrToGoString(result.QueryPtr),
		Target: cCharPtrToGoString(result.TargetPtr),
		Score:  0,
		Length: 0,
	}
}

func convertCResultToResult(cResult C.struct_Result) Result {
	return Result{
		QueryPtr:  cResult.query_ptr,
		TargetPtr: cResult.target_ptr,
	}
}

// TODO: This should free the C strings
func FreeAlignmentResult(query *C.char, target *C.char) {
	C.free_alignment_result(query, target)
}

// TODO: Ask someone, is this neccassary?
func FreeCString(cStr *C.char) {
	C.free_c_string(cStr)
}
