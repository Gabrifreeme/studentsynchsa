import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the exact line where data is emitted to the frontend
emit_idx = None
for i, line in enumerate(lines):
    if "socketio.emit('terminal_output', data)" in line:
        emit_idx = i
        break

assert emit_idx is not None, "Could not find socketio.emit('terminal_output')"

eol = "\r\n" if lines[emit_idx].endswith("\r\n") else "\n"

# Insert the ANSI strip logic right before the emit
strip_code = (
    "                # STRIP ANSI CURSOR CODES TO FIX FLOATING TEXT" + eol +
    "                import re" + eol +
    "                data = re.sub(r'\\x1b\\[[0-9;]*[CH]', '', data)" + eol
)

lines.insert(emit_idx, strip_code)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Injected ANSI filter before socketio.emit at line {emit_idx+1}")
