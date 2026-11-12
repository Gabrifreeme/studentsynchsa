import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[15320].endswith("\r\n") else "\n"

# Verify boundaries (1-indexed 15321-15327 -> 0-indexed 15320-15326)
assert "STRIP ANSI" in lines[15320], f"L15321 mismatch: {lines[15320]!r}"
assert "socketio.emit('terminal_output', clean_data)" in lines[15326], f"L15327 mismatch: {lines[15326]!r}"

indent = "                    "

new_block = (
    indent + "# Strip ALL ANSI escape sequences" + eol +
    indent + "import re" + eol +
    indent + "clean_data = re.sub(r'\\x1b\\[[0-9;?]*[A-Za-z]|\\^\\[\\[?[0-9;]*[A-Za-z]|\\x1b[\\]P^_][^\\x07]*\\x07', '', data)" + eol +
    indent + "socketio.emit('terminal_output', clean_data)" + eol
)

new_lines = lines[:15320] + [new_block] + lines[15327:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Replaced 7 lines with clean regex at 15321-15323")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
