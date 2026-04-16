import re

with open("crates/kalpixk-core/src/security.rs", "r") as f:
    content = f.read()

# Find the tests module
test_match = re.search(r"mod tests \{", content)
if test_match:
    tests_start = test_match.start()
    tests_end = content.rfind("}")

    tests_block = content[tests_start:tests_end+1]
    pre_block = content[:tests_start]
    post_block = content[tests_end+1:]

    # Move everything from post_block to before tests_block
    new_content = pre_block + post_block + "\n\n" + tests_block

    with open("crates/kalpixk-core/src/security.rs", "w") as f:
        f.write(new_content)
