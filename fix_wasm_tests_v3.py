import re
with open("crates/kalpixk-core/tests/wasm_tests.rs", "r") as f:
    lines = f.readlines()

new_lines = []
skip = 0
for i, line in enumerate(lines):
    if skip > 0:
        skip -= 1
        continue
    if "let result = kalpixk_core::parse_log_line(raw, source).expect(&format!(" in line:
        new_lines.append('    let result = kalpixk_core::parse_log_line(raw, source).unwrap_or_else(|| panic!("parse_log_line should succeed for source={}", source));\n')
        # Check how many lines to skip
        if "source" in lines[i+1] and "));" in lines[i+2]:
            skip = 2
        elif "));" in lines[i+1]:
            skip = 1
    else:
        new_lines.append(line)

with open("crates/kalpixk-core/tests/wasm_tests.rs", "w") as f:
    f.writelines(new_lines)
