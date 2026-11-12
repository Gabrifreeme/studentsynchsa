import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Sanity: verify the boundary lines (1-indexed 15299-15319 -> 0-indexed 15298-15318)
assert "@socketio.on('connect')" in lines[15298], f"Line 15299 mismatch: {lines[15298]!r}"
assert "socketio.start_background_task(read_output)" in lines[15318], f"Line 15319 mismatch: {lines[15318]!r}"

eol = "\r\n" if lines[15298].endswith("\r\n") else "\n"

new_block = (
    "@socketio.on('connect')" + eol +
    "def handle_connect():" + eol +
    "    global terminal_process" + eol +
    "    # Kill old PTY if any (prevents ghost buffers on reopen)" + eol +
    "    if terminal_process:" + eol +
    "        try:" + eol +
    "            terminal_process.terminate(force=True)" + eol +
    "        except Exception:" + eol +
    "            pass" + eol +
    "        terminal_process = None" + eol +
    "    # Spawn fresh PowerShell" + eol +
    "    os.environ['TERM'] = 'xterm-256color'" + eol +
    "    terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')" + eol +
    "    # Force initial dimensions" + eol +
    "    try:" + eol +
    "        terminal_process.setwinsize(24, 80)" + eol +
    "    except Exception:" + eol +
    "        pass" + eol +
    "    def read_output():" + eol +
    "        while terminal_process and terminal_process.isalive():" + eol +
    "            try:" + eol +
    "                data = terminal_process.read(1024)" + eol +
    "                if data:" + eol +
    "                    socketio.emit('terminal_output', data)" + eol +
    "            except EOFError:" + eol +
    "                break" + eol +
    "            except Exception:" + eol +
    "                break" + eol +
    "    socketio.start_background_task(read_output)" + eol
)

new_lines = lines[:15298] + [new_block] + lines[15319:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: handle_connect replaced at lines 15299-15319")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
