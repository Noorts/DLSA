use std::process::Command;

fn get_hash() -> String {
    let output = Command::new("git")
        .args(&["rev-parse", "--short", "HEAD"])
        .output()
        .expect("Could not get git hash");
    String::from_utf8(output.stdout).expect("Could not parse git hash")
}

fn main() {
    println!("cargo:rustc-env=GIT_HASH={}", get_hash());
}
