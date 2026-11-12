import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11333].endswith("\r\n") else "\n"

# Verify (1-indexed 11334 -> 0-indexed 11333)
assert "term.write(data)" in lines[11333], f"L11334 mismatch: {lines[11333]!r}"

# Insert the log line before term.write
log_line = "        console.log('RAW IN:', JSON.stringify(data));" + eol
lines.insert(11333, log_line)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: console.log at line 11334")
