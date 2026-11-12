import io, re

py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Regex to find the entire handle_connect function
pattern = r"@socketio\.on\('connect'\)\ndef handle_connect\(\):.*?(?=@socketio\.on|socketio\.run|if __name__)"
match = re.search(pattern, py, re.DOTALL)

if match:
    new_connect = """@socketio.on('connect')
def handle_connect():
    global terminal_process
    
    # 1. KILL the old PTY if it exists (prevents ghost buffers)
    if terminal_process:
        try:
            terminal_process.terminate(force=True)
        except Exception:
            pass
        terminal_process = None

    # 2. Spawn a fresh PowerShell
    import os
    os.environ['TERM'] = 'xterm-256color'
    terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')

    # 3. Force initial dimensions immediately
    try:
        terminal_process.setwinsize(24, 80)
    except Exception:
        pass

    # 4. Start a brand new reader thread
    def read_output():
        while terminal_process and terminal_process.isalive():
            try:
                data = terminal_process.read(1024)
                if data:
                    socketio.emit('terminal_output', data)
            except EOFError:
                break
            except Exception:
                break

    socketio.start_background_task(read_output)

"""
    py = py[:match.start()] + new_connect + py[match.end():]
    print("BACKEND: Rewrote handle_connect to hard-reset PTY on every connection")
else:
    print("BACKEND: WARNING - Could not find handle_connect block")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
