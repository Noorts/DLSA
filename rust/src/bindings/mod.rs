use std::ffi::{c_char, CStr, CString};

use crate::algorithm::AlignmentScores;

const LANES: usize = 64;

#[repr(C)]
pub struct AlignmentResult {
    query: *mut c_char,
    target: *mut c_char,
}

const SCORES : AlignmentScores = AlignmentScores {
    gap: -2,
    r#match: 3,
    miss: -3,
};

#[no_mangle]
extern "C" fn test_binding() {
    println!("Hello world");
}
#[no_mangle]
extern "C" fn test_write(_target_res_ptr: *mut c_char, _size: usize) -> AlignmentResult {
    let query = CString::new("Hoi").unwrap();
    let target = CString::new("Doei").unwrap();
    let data = AlignmentResult {
        query: query.into_raw(),
        target: target.into_raw(),
    };

    return data;
}

/// Find a local alignment using a parallel implementation
///
/// Note: If SIMD is available for your platform, you probably want to use that
/// version instead, it has better performance on a single core than the
/// the theoretical performance max from this implementation.
///
/// Arguments:
/// * query_ptr: A pointer to a alignment query. Should be a valid UTF-8 string.
/// * target_ptr: A pointer to a alignment target. Should be a valid UTF-8 string.
/// * threads: The amount of threads to run on.
/// * query_res_ptr: A pointer to a memory allocation of at least length: query string
/// * target_res_ptr: A pointer to a memory allocation of at least length: target string
#[no_mangle]
pub extern "C" fn find_alignment_parallel(
    query_ptr: *const c_char,
    target_ptr: *const c_char,
    threads: usize,
) -> AlignmentResult {
    // TODO: Rust chars are in our case a fine approximation as our values are always ascii, but
    // probably not the best idea to use them as this is not necessarily the case across the c ABI.
    // However a proper implementation should not care about it anyway as long as it implements Eq
    // and is indexable. For now the assumption is that the input data has to be valid UTF-8 that
    // would be indexable.
    let query: &[char] = unsafe { std::mem::transmute(CStr::from_ptr(query_ptr).to_bytes()) };
    let target: &[char] = unsafe { std::mem::transmute(CStr::from_ptr(target_ptr).to_bytes()) };

    let (query_res, target_res) = crate::find_alignment_parallel(query, target, threads);

    let query_res_ref: &[char] = query_res.as_ref();
    let target_res_ref: &[char] = target_res.as_ref();

    assert!(query.len() >= query_res.len());
    assert!(target.len() >= target_res.len());

    let q_c_slice: &[u8] = unsafe { std::mem::transmute(query_res_ref) };
    let t_c_slice: &[u8] = unsafe { std::mem::transmute(target_res_ref) };

    AlignmentResult {
        query: CString::new(q_c_slice).unwrap().into_raw(),
        target: CString::new(t_c_slice).unwrap().into_raw(),
    }
}

#[no_mangle]
pub extern "C" fn find_alignment_simd(
    query_ptr: *const c_char,
    target_ptr: *const c_char,
) -> AlignmentResult {
    let query: &[u8] = unsafe { CStr::from_ptr(query_ptr).to_bytes() };
    let target: &[u8] = unsafe { CStr::from_ptr(target_ptr).to_bytes() };

    let query: Vec<char> = String::from_utf8(query.to_vec()).unwrap().chars().collect();
    let target: Vec<char> = String::from_utf8(target.to_vec())
        .unwrap()
        .chars()
        .collect();

    println!("Searching for alignment: Q: {query:?}; T: {target:?}");

    let (query_res, target_res) = crate::find_alignment_simd::<LANES>(&query, &target, SCORES);

    let query_res_ref: &[char] = query_res.as_ref();
    let target_res_ref: &[char] = target_res.as_ref();

    println!("Found alignment Q: {query_res:?}; T: {target_res:?}");

    let q_res: String = query_res_ref.into_iter().collect();
    let t_res: String = target_res_ref.into_iter().collect();

    AlignmentResult {
        query: CString::new(q_res.into_bytes()).unwrap().into_raw(),
        target: CString::new(t_res.into_bytes()).unwrap().into_raw(),
    }
}

// #[no_mangle]
// pub extern "C" fn find_alignment_sequential(
//     query_ptr: *const c_char,
//     target_ptr: *const c_char,
// ) -> AlignmentResult {
//     todo!();
//     // let query: &[u8] = unsafe { CStr::from_ptr(query_ptr).to_bytes() };
//     // // let target: &[char] = unsafe { std::mem::transmute(CStr::from_ptr(target_ptr).to_bytes()) };
//     //
//     // let query: Vec<char> = String::from_utf8(query.to_vec()).unwrap().chars().collect();
//     //
//     // let (query_res, target_res) = crate::find_alignment_sequential(&query, target);
//     //
//     // let query_res_ref: &[char] = query_res.as_ref();
//     // let target_res_ref: &[char] = target_res.as_ref();
//     //
//     // assert!(query.len() >= query_res.len());
//     // assert!(target.len() >= target_res.len());
//     //
//     // let q_c_slice: &[u8] = unsafe { std::mem::transmute(query_res_ref) };
//     // let t_c_slice: &[u8] = unsafe { std::mem::transmute(target_res_ref) };
//     //
//     // AlignmentResult {
//     //     query: CString::new(q_c_slice).unwrap().into_raw(),
//     //     target: CString::new(t_c_slice).unwrap().into_raw(),
//     // }
// }

#[no_mangle]
pub extern "C" fn find_alignment_sequential_straight(
    query_ptr: *const c_char,
    target_ptr: *const c_char,
) -> AlignmentResult {
    let query: &[u8] = unsafe { CStr::from_ptr(query_ptr).to_bytes() };
    let target: &[u8] = unsafe { CStr::from_ptr(target_ptr).to_bytes() };

    let query: Vec<char> = String::from_utf8(query.to_vec()).unwrap().chars().collect();
    let target: Vec<char> = String::from_utf8(target.to_vec())
        .unwrap()
        .chars()
        .collect();

    // println!("Searching for alignment: Q: {query:?}; T: {target:?}");

    let (query_res, target_res) = crate::find_alignment_sequential_straight(&query, &target, SCORES);

    let query_res_ref: &[char] = query_res.as_ref();
    let target_res_ref: &[char] = target_res.as_ref();

    // println!("Found alignment Q: {query_res:?}; T: {target_res:?}");

    let q_res: String = query_res_ref.into_iter().collect();
    let t_res: String = target_res_ref.into_iter().collect();

    AlignmentResult {
        query: CString::new(q_res.into_bytes()).unwrap().into_raw(),
        target: CString::new(t_res.into_bytes()).unwrap().into_raw(),
    }
}
