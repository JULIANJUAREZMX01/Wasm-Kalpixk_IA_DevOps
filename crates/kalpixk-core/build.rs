fn main() {
    // Allow undefined symbols in WASM to support importing Zig Metal Core functions from the host environment
    // or from other linked modules. This is required when Zig compilation is handled externally.
    println!("cargo:rustc-link-arg=--allow-undefined");
}
