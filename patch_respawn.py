import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

start_idx = None
for i, line in enumerate(lines):
    if "def handle_terminal_input(data):" in line:
        start_idx = i
        break

assert start_idx is not None

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"

end_idx = start_idx + 1
while end_idx < len(lines) and not lines[end_idx].startswith("@socketio"):
    end_idx += 1

# Full handler: kill on Ctrl+C, respawn if dead before any other command
new_handler = (
    "def handle_terminal_input(data):" + eol +
    "    global terminal_process" + eol +
    "    if data == '\\x03':" + eol +
    "        # Ctrl+C - kill the PTY" + eol +
    "        if terminal_process:" + eol +
    "            try:" + eol +
    "                terminal_process.terminate(force=True)" + eol +
    "            except Exception:" + eol +
    "                pass" + eol +
    "            terminal_process = None" + eol +
    "        return" + eol +
    "    # Respawn PTY if dead (from Ctrl+C or crash)" + eol +
    "    if not terminal_process or not terminal_process.isalive():" + eol +
    "        try:" + eol +
    "            os.environ['TERM'] = 'xterm-256color'" + eol +
    "            terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile')" + eol +
    "            try: terminal_process.setwinsize(24, 80)" + eol +
    "            except: pass" + eol +
    "            def read_output_r():" + eol +
    "                while terminal_process and terminal_process.isalive():" + eol +
    "                    try:" + eol +
    "                        d = terminal_process.read(1024)" + eol +
    "                        if d:" + eol +
    "                            import re as _re" + eol +
    "                            clean = _re.sub(r'\\x1b\\[[0-9;?]*[A-Za-z]', '', d)" + eol +
    "                            socketio.emit('terminal_output', clean)" + eol +
    "                    except Exception:" + eol +
    "                        break" + eol +
    "            socketio.start_background_task(read_output_r)" + eol +
    "        except Exception:" + eol +
    "            pass" + eol +
    "    try:" + eol +
    "        terminal_process.write(data)" + eol +
    "    except Exception:" + eol +
    "        pass" + eol
)

lines[start_idx:end_idx] = [new_handler]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("SPLICE OK: Backend Ctrl+C kills PTY, next command respawns")
