import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[15283].endswith("\r\n") else "\n"

# Verify (1-indexed 15284 -> 0-indexed 15283)
assert "global terminal_process, _current_subprocess" in lines[15283], f"L15284 mismatch: {lines[15283]!r}"
assert lines[15298].strip() == "pass", f"L15299 mismatch: {lines[15298]!r}"

new_block = (
    "    global terminal_process" + eol +
    "    if data == '\\x03':" + eol +
    "        # Ctrl+C pressed - kill the PowerShell PTY" + eol +
    "        if terminal_process:" + eol +
    "            try:" + eol +
    "                terminal_process.terminate(force=True)" + eol +
    "            except Exception:" + eol +
    "                pass" + eol +
    "            terminal_process = None" + eol +
    "        # Re-spawn a fresh PowerShell for the next command" + eol +
    "        try:" + eol +
    "            os.environ['TERM'] = 'xterm-256color'" + eol +
    "            terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile')" + eol +
    "            try: terminal_process.setwinsize(24, 80)" + eol +
    "            except: pass" + eol +
    "            # Restart the reader thread" + eol +
    "            def read_output_c():" + eol +
    "                while terminal_process and terminal_process.isalive():" + eol +
    "                    try:" + eol +
    "                        d = terminal_process.read(1024)" + eol +
    "                        if d:" + eol +
    "                            import re as _re" + eol +
    "                            clean = _re.sub(r'\\x1b\\[[0-9;?]*[A-Za-z]', '', d)" + eol +
    "                            socketio.emit('terminal_output', clean)" + eol +
    "                    except Exception:" + eol +
    "                        break" + eol +
    "            socketio.start_background_task(read_output_c)" + eol +
    "        except Exception:" + eol +
    "            pass" + eol +
    "        return" + eol +
    "    if not terminal_process or not terminal_process.isalive():" + eol +
    "        return" + eol +
    "    try:" + eol +
    "        terminal_process.write(data)" + eol +
    "    except Exception:" + eol +
    "        pass" + eol
)

new_lines = lines[:15283] + [new_block] + lines[15299:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Ctrl+C kills and respawns PTY")
