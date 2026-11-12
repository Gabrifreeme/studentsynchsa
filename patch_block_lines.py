import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11293].endswith("\r\n") else "\n"

# Verify
assert "socket.on('terminal_output'" in lines[11293], f"L11294 mismatch: {lines[11293]!r}"
assert "data === '\\x03'" in lines[11365], f"L11366 mismatch: {lines[11365]!r}"
assert "data === '\\r'" in lines[11372], f"L11373 mismatch: {lines[11372]!r}"

# Insert lines bottom-up so indices don't shift

# 1. Line 11374 (0-indexed 11373) - add block clear on Enter
lines.insert(11373, "            window._blockOutput = false;" + eol)

# 2. Line 11370 (0-indexed 11369) - add block set on Ctrl+C
lines.insert(11369, "            window._blockOutput = true;" + eol)

# 3. Line 11295 (0-indexed 11294) - add block check in terminal_output
lines.insert(11294, "        if (window._blockOutput) { return; }" + eol)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("SPLICE OK: Block output on Ctrl+C, unblock on Enter")
