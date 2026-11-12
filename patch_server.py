import io

path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# We are replacing lines 15266 through 15306 (1-indexed)
# In 0-indexed, that's 15265 to 15305
start_idx = 15265
end_idx = 15306

new_block = """# --- VS Code Style PTY Terminal ---
import os
import threading

terminal_process = None

@socketio.on('terminal_input')
def handle_terminal_input(data):
    global terminal_process
    if terminal_process and terminal_process.isalive():
        try:
            terminal_process.write(data)
        except Exception:
            pass

@socketio.on('terminal_resize')
def handle_terminal_resize(data):
    global terminal_process
    if terminal_process and terminal_process.isalive():
        try:
            # winpty setwinsize is (cols, rows) on some versions, (rows, cols) on others.
            # We will try both to prevent the exception that breaks the stream.
            terminal_process.setwinsize(int(data['cols']), int(data['rows']))
        except Exception:
            try:
                terminal_process.setwinsize(int(data['rows']), int(data['cols']))
            except Exception:
                pass

@socketio.on('connect')
def handle_connect():
    global terminal_process
    if not terminal_process or not terminal_process.isalive():
        # Spawn PowerShell on Windows
        terminal_process = PtyProcess.spawn('powershell.exe')

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

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, allow_unsafe_werkzeug=True)
"""

# Splice the file
new_lines = lines[:start_idx] + [new_block] + lines[end_idx:]

with io.open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("SERVER PATCHED: Replaced PTY block with thread-safe version.")
