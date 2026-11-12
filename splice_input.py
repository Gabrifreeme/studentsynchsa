import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the @socketio.on('terminal_input') block
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "@socketio.on('terminal_input')" in line:
        start_idx = i
    if start_idx is not None and i > start_idx and line.startswith("@socketio.on("):
        end_idx = i - 1
        break

assert start_idx is not None, "Could not find terminal_input"

if end_idx is None:
    end_idx = start_idx + 6

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"

new_block = (
    "@socketio.on('terminal_input')" + eol +
    "def handle_terminal_input(data):" + eol +
    "    global terminal_process" + eol +
    "    if terminal_process and terminal_process.isalive():" + eol +
    "        try:" + eol +
    "            # Force carriage return to be a real byte, not escaped string" + eol +
    "            if data == '\\\\r' or data == '\\\\r\\\\n':" + eol +
    "                terminal_process.write('\\r')" + eol +
    "            else:" + eol +
    "                terminal_process.write(data)" + eol +
    "        except Exception:" + eol +
    "            pass" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx + 1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: terminal_input replaced at lines {start_idx+1}-{end_idx+1}")
