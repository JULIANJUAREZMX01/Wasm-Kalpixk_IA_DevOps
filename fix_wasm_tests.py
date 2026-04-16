with open("crates/kalpixk-core/tests/wasm_tests.rs", "r") as f:
    content = f.read()

content = content.replace('.expect(&format!("parse_log_line should succeed for source={}", source))', '.unwrap_or_else(|| panic!("parse_log_line should succeed for source={}", source))')
content = content.replace('v >= 0.0 && v <= 1.0', '(0.0..=1.0).contains(&v)')
content = content.replace('parsed <= 3 && parsed >= 1', '(1..=3).contains(&parsed)')

with open("crates/kalpixk-core/tests/wasm_tests.rs", "w") as f:
    f.write(content)
