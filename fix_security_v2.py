import re

with open("crates/kalpixk-core/src/security.rs", "r") as f:
    lines = f.readlines()

# Find test module and SourceRateLimiter implementation
test_start_line = -1
impl_start_line = -1

for i, line in enumerate(lines):
    if "mod tests {" in line:
        test_start_line = i
    if "impl SourceRateLimiter {" in line and i > test_start_line and test_start_line != -1:
        impl_start_line = i

if test_start_line != -1 and impl_start_line != -1:
    # Everything from impl_start_line to end
    impl_block = lines[impl_start_line:]

    # Backtrack to find the #[cfg(test)] above tests
    cfg_test_line = test_start_line
    if cfg_test_line > 0 and "#[cfg(test)]" in lines[cfg_test_line-1]:
        cfg_test_line -= 1

    # New content: part before cfg_test_line + impl_block + cfg_test_line to impl_start_line
    new_lines = lines[:cfg_test_line] + impl_block + ["\n"] + lines[cfg_test_line:impl_start_line]

    with open("crates/kalpixk-core/src/security.rs", "w") as f:
        f.writelines(new_lines)

# Fix lib.rs boolean expressions
with open("crates/kalpixk-core/src/lib.rs", "r") as f:
    lib_content = f.read()

lib_content = lib_content.replace("!security::validate_raw_log(raw).is_ok()", "security::validate_raw_log(raw).is_err()")
lib_content = lib_content.replace("!security::validate_raw_log(line).is_ok()", "security::validate_raw_log(line).is_err()")

with open("crates/kalpixk-core/src/lib.rs", "w") as f:
    f.write(lib_content)
