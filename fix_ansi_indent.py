import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[15320].endswith("\r\n") else "\n"

# Verify (1-indexed 15321-15325 -> 0-indexed 15320-15324)
assert "if data:" in lines[15320], f"L15321 mismatch: {lines[15320]!r}"
assert "STRIP ANSI" in lines[15321], f"L15322 mismatch: {lines[15321]!r}"
assert "terminal_output" in lines[15324], f"L15325 mismatch: {lines[15324]!r}"

# Replace 5 lines with properly-indented block (20 spaces = 5 levels inside the function)
new_block = (
    "                if data:" + eol +
    "                    # STRIP ANSI CURSOR CODES TO FIX FLOATING TEXT" + eol +
    "                    import re" + eol +
    "                    data = re.sub(r'\\x1b\\[[0-9;]*[CH]', '', data)" + eol +
    "                    socketio.emit('terminal_output', data)" + eol
)

new_lines = lines[:15320] + [new_block] + lines[15325:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Fixed indentation, ANSI strip properly nested")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
