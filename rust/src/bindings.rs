use std::convert::TryFrom;
use std::ffi::{c_char, CStr, CString};
use std::panic::{self, AssertUnwindSafe};
use crate::algorithm::AlignmentScores;
use crate::algorithm::find_alignment_simd_lowmem;

const LANES: usize = 64;

#[repr(C)]
pub struct AlignmentResult {
    query: *mut c_char,
    target: *mut c_char,
    score: i16,
    max_x: u64,
    max_y: u64
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
// #[no_mangle]
// pub extern "C" fn find_alignment_parallel(
//     query_ptr: *const c_char,
//     target_ptr: *const c_char,
//     threads: usize,
// ) -> AlignmentResult {
//     // TODO: Rust chars are in our case a fine approximation as our values are always ascii, but
//     // probably not the best idea to use them as this is not necessarily the case across the c ABI.
//     // However a proper implementation should not care about it anyway as long as it implements Eq
//     // and is indexable. For now the assumption is that the input data has to be valid UTF-8 that
//     // would be indexable.
//     let result = panic::catch_unwind(AssertUnwindSafe(|| { 
        
//         let query: &[char] = unsafe { std::mem::transmute(CStr::from_ptr(query_ptr).to_bytes()) };
//         let target: &[char] = unsafe { std::mem::transmute(CStr::from_ptr(target_ptr).to_bytes()) };

//         let (query_res, target_res) = crate::find_alignment_parallel(query, target, threads);

//         let query_res_ref: &[char] = query_res.as_ref();
//         let target_res_ref: &[char] = target_res.as_ref();

//         assert!(query.len() >= query_res.len());
//         assert!(target.len() >= target_res.len());

//         let q_c_slice: &[u8] = unsafe { std::mem::transmute(query_res_ref) };
//         let t_c_slice: &[u8] = unsafe { std::mem::transmute(target_res_ref) };

//         let res = Box::new(AlignmentResult {
//             query: CString::new(q_res.into_bytes()).unwrap().into_raw(),
//             target: CString::new(t_res.into_bytes()).unwrap().into_raw(),

//         });
//         panic!("test");
//         Box::into_raw(res)
//     }));
//     match result {
//         Ok(ptr) => ptr,
//         Err(_) => std::ptr::null_mut() // Return a null pointer on panic
//     }
// }

#[no_mangle]
pub unsafe extern "C" fn find_alignment_simd(
    query_ptr: *const c_char,
    target_ptr: *const c_char,
    alignment_scores: AlignmentScores,
) -> *mut AlignmentResult {
    let result = panic::catch_unwind(AssertUnwindSafe(|| { 
        let query: &[u8] = unsafe { CStr::from_ptr(query_ptr).to_bytes() };
        let target: &[u8] = unsafe { CStr::from_ptr(target_ptr).to_bytes() };

        let query: Vec<char> = String::from_utf8(query.to_vec()).unwrap().chars().collect();
        let target: Vec<char> = String::from_utf8(target.to_vec())
            .unwrap()
            .chars()
            .collect();

        // println!("Searching for alignment: Q: {query:?}; T: {target:?}");

        let (query_res, target_res, score, max_x, max_y) = crate::find_alignment_simd::<LANES>(&query, &target, alignment_scores);

        let query_res_ref: &[char] = query_res.as_ref();
        let target_res_ref: &[char] = target_res.as_ref();

        // println!("Found alignment Q: {query_res:?}; T: {target_res:?}");

        let q_res: String = query_res_ref.iter().collect();
        let t_res: String = target_res_ref.iter().collect();

        let res = Box::new(AlignmentResult {
            query: CString::new(q_res.into_bytes()).unwrap().into_raw(),
            target: CString::new(t_res.into_bytes()).unwrap().into_raw(),
            score,
            max_x: u64::try_from(max_x).unwrap(),
            max_y: u64::try_from(max_y).unwrap()
        });

        Box::into_raw(res)
    }));
    match result {
        Ok(ptr) => ptr,
        Err(_) => std::ptr::null_mut() 
    }
}

#[no_mangle]
pub unsafe extern "C" fn find_alignment_low_memory(
    query_ptr: *const c_char,
    target_ptr: *const c_char,
    alignment_scores: AlignmentScores,
) -> *mut AlignmentResult {
    let result = panic::catch_unwind(AssertUnwindSafe(|| { 
        let query: &[u8] = unsafe { CStr::from_ptr(query_ptr).to_bytes() };
        let target: &[u8] = unsafe { CStr::from_ptr(target_ptr).to_bytes() };

        let query: Vec<char> = String::from_utf8(query.to_vec()).unwrap().chars().collect();
        let target: Vec<char> = String::from_utf8(target.to_vec())
            .unwrap()
            .chars()
            .collect();

        // println!("Searching for alignment: Q: {query:?}; T: {target:?}");

        let (query_res, target_res, score, max_x, max_y) = find_alignment_simd_lowmem::<LANES>(&query, &target, alignment_scores);

        let query_res_ref: &[char] = query_res.as_ref();
        let target_res_ref: &[char] = target_res.as_ref();

        // println!("Found alignment Q: {query_res:?}; T: {target_res:?}");

        let q_res: String = query_res_ref.iter().collect();
        let t_res: String = target_res_ref.iter().collect();

        let res = Box::new(AlignmentResult {
            query: CString::new(q_res.into_bytes()).unwrap().into_raw(),
            target: CString::new(t_res.into_bytes()).unwrap().into_raw(),
            score,
            max_x: u64::try_from(max_x).unwrap(),
            max_y: u64::try_from(max_y).unwrap()
        });

        Box::into_raw(res)
    }));
    match result {
        Ok(ptr) => ptr,
        Err(_) => std::ptr::null_mut() 
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
pub unsafe extern "C" fn find_alignment_sequential_straight(
    query_ptr: *const c_char,
    target_ptr: *const c_char,
    alignment_scores: AlignmentScores,
) -> AlignmentResult {
    let query: &[u8] = unsafe { CStr::from_ptr(query_ptr).to_bytes() };
    let target: &[u8] = unsafe { CStr::from_ptr(target_ptr).to_bytes() };

    let query: Vec<char> = String::from_utf8(query.to_vec()).unwrap().chars().collect();
    let target: Vec<char> = String::from_utf8(target.to_vec())
        .unwrap()
        .chars()
        .collect();

    // println!("Searching for alignment: Q: {query:?}; T: {target:?}");

    let (query_res, target_res, score, max_x, max_y) = crate::find_alignment_sequential_straight(&query, &target, alignment_scores);

    let query_res_ref: &[char] = query_res.as_ref();
    let target_res_ref: &[char] = target_res.as_ref();

    // println!("Found alignment Q: {query_res:?}; T: {target_res:?}");

    let q_res: String = query_res_ref.iter().collect();
    let t_res: String = target_res_ref.iter().collect();

    AlignmentResult {
        query: CString::new(q_res.into_bytes()).unwrap().into_raw(),
        target: CString::new(t_res.into_bytes()).unwrap().into_raw(),
        score,
        max_x: u64::try_from(max_x).unwrap(),
        max_y: u64::try_from(max_y).unwrap()
    }
}

//functions to free the memory allocated by the rust code
#[no_mangle]
pub unsafe extern "C" fn free_alignment_result(alignment_result_ptr: *mut AlignmentResult) {
    unsafe {
        if alignment_result_ptr.is_null() {
            return;
        }
        let _ = Box::from_raw(alignment_result_ptr);
    }
}

#[no_mangle]
pub unsafe extern "C" fn free_c_string(c_str_ptr: *mut c_char) {
    unsafe {
        if !c_str_ptr.is_null() {
            let _ = CString::from_raw(c_str_ptr);
        }
    }
}
