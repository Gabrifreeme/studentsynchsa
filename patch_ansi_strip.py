import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the emit line inside read_output
emit_idx = None
for i, line in enumerate(lines):
    if "socketio.emit('terminal_output', data)" in line:
        emit_idx = i
        break

assert emit_idx is not None, "Could not find socketio.emit('terminal_output')"

eol = "\r\n" if lines[emit_idx].endswith("\r\n") else "\n"

# Replace the emit line with one that strips ANSI codes first
old_emit = lines[emit_idx]
indent = old_emit[:len(old_emit) - len(old_emit.lstrip())]

new_emit = (
    indent + "import re" + eol +
    indent + "# Strip all ANSI escape codes to prevent screen jumping" + eol +
    indent + "clean_data = re.sub(r'\\x1b\\[[0-9;?]*[A-Za-z]', '', data)" + eol +
    indent + "socketio.emit('terminal_output', clean_data)" + eol
)

lines[emit_idx] = new_emit

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Added ANSI stripping at line {emit_idx+1}")
