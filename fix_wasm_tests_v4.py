with open("crates/kalpixk-core/tests/wasm_tests.rs", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "));" in line and len(line.strip()) == 3:
        continue
    new_lines.append(line)

with open("crates/kalpixk-core/tests/wasm_tests.rs", "w") as f:
    f.writelines(new_lines)
