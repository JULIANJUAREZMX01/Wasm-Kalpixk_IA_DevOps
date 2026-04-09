#!/bin/bash
set -e
cargo build --target wasm32-wasip1 --release
echo "Build complete."
