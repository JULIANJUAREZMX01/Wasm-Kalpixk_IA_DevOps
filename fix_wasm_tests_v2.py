import re
with open("crates/kalpixk-core/tests/wasm_tests.rs", "r") as f:
    content = f.read()

# Pattern for the multi-line expect
pattern = r'\.expect\(&format\(\s*"parse_log_line should succeed for source=\{\}",\s*source\s*\)\)'
content = re.sub(pattern, r'.unwrap_or_else(|| panic!("parse_log_line should succeed for source={}", source))', content, flags=re.MULTILINE)

with open("crates/kalpixk-core/tests/wasm_tests.rs", "w") as f:
    f.write(content)
