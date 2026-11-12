import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the terminal_input handler
start_idx = None
for i, line in enumerate(lines):
    if "@socketio.on('terminal_input')" in line:
        start_idx = i
        break

assert start_idx is not None, "Could not find terminal_input handler"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"

# Find the end of the handler (next @socketio.on)
end_idx = start_idx + 1
while end_idx < len(lines) and not lines[end_idx].startswith("@socketio"):
    end_idx += 1

# Replace the whole handler with one that tracks and kills the process
new_handler = (
    "@socketio.on('terminal_input')" + eol +
    "def handle_terminal_input(data):" + eol +
    "    global terminal_process, _current_subprocess" + eol +
    "    if data == '\\x03':" + eol +
    "        # Ctrl+C pressed - kill the running subprocess" + eol +
    "        if _current_subprocess:" + eol +
    "            try:" + eol +
    "                _current_subprocess.kill()" + eol +
    "            except Exception:" + eol +
    "                pass" + eol +
    "            _current_subprocess = None" + eol +
    "        return" + eol +
    "    if not terminal_process or not terminal_process.isalive():" + eol +
    "        return" + eol +
    "    try:" + eol +
    "        terminal_process.write(data)" + eol +
    "    except Exception:" + eol +
    "        pass" + eol
)

lines[start_idx:end_idx] = [new_handler]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("BACKEND: Replaced terminal_input handler to kill subprocess on Ctrl+C")
