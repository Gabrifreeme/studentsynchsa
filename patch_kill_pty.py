import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the start of the terminal_input handler
start_idx = None
for i, line in enumerate(lines):
    if "def handle_terminal_input(data):" in line:
        start_idx = i
        break

assert start_idx is not None, "Could not find handle_terminal_input"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"

# Find the end of the handler (next @socketio.on)
end_idx = start_idx + 1
while end_idx < len(lines) and not lines[end_idx].startswith("@socketio"):
    end_idx += 1

# Replace it entirely with a version that kills the process on Ctrl+C
new_handler = (
    "def handle_terminal_input(data):" + eol +
    "    global terminal_process" + eol +
    "    if data == '\\x03':" + eol +
    "        if terminal_process:" + eol +
    "            try:" + eol +
    "                terminal_process.terminate(force=True)" + eol +
    "            except Exception:" + eol +
    "                pass" + eol +
    "            terminal_process = None" + eol +
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
print(f"SPLICE OK: backend Ctrl+C kills PTY")
