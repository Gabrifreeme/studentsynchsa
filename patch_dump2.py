import io

py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Sanity check: Verify line 15311 is the emit line
assert "socketio.emit('terminal_output', data)" in lines[15310], f"Line 15311 mismatch: {lines[15310]!r}"

# Determine line ending
eol = "\r\n" if lines[15310].endswith("\r\n") else "\n"

# Inject debug print BEFORE the emit
debug_line = '                        print(f"PTY OUT: {repr(data)}")' + eol

# Insert at index 15310 (which is line 15311)
lines.insert(15310, debug_line)

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("BACKEND: Injected PTY OUT debug print at line 15311.")
