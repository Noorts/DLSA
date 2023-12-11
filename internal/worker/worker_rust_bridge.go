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
}

func cCharPtrToString(cStr *C.char) string {
	return C.GoString(cStr)
}

func ConvertResultToGoResult(cResult *C.struct_Result) GoResult {
	query := cCharPtrToString(cResult.query_ptr)
	target := cCharPtrToString(cResult.target_ptr)

	return GoResult{
		Query:  query,
		Target: target,
	}
}

// TODO: Some kind of logic to determine whether to use low mem, simd, or just sequential
func FindRustAlignmentParallel(query, target string) GoResult {
	queryC := C.CString(query)
	targetC := C.CString(target)

	threads := C.ulong(4)
	cResult_ref := C.find_alignment_parallel(queryC, targetC, threads)
	goResult := convertResultToGoResult(cResult_ref)

	defer FreeAlignmentResult(cResult_ref)

	return goResult
}

func FindRustAlignmentSequential(query, target string) GoResult {
	queryC := C.CString(query)
	targetC := C.CString(target)

	cResult_ref := C.find_alignment_sequential_straight(queryC, targetC)

	goResult := convertResultToGoResult(cResult_ref)

	defer FreeAlignmentResult(cResult_ref)

	return goResult
}

func FindRustAlignmentSimd(query, target string) GoResult {
	queryC := C.CString(query)
	targetC := C.CString(target)

	cResult := C.find_alignment_simd(queryC, targetC)
	defer FreeAlignmentResult(cResult)

	return convertResultToGoResult(cResult)
}

func cCharPtrToGoString(cStr *C.char) string {
	return C.GoString(cStr)
}

// TODO: Length and score
func convertResultToGoResult(cResult *C.struct_Result) GoResult {
	return GoResult{
		Query:  cCharPtrToGoString(cResult.query_ptr),
		Target: cCharPtrToGoString(cResult.target_ptr),
		Score:  0,
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
