import io

py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Find the read_output function and inject print(repr(data))
old_read = """                    data = terminal_process.read(1024)
                    if data:
                        socketio.emit('terminal_output', data)"""

new_read = """                    data = terminal_process.read(1024)
                    if data:
                        print(f"PTY OUT: {repr(data)}")  # <--- NEW DEBUG LINE
                        socketio.emit('terminal_output', data)"""

if old_read in py:
    py = py.replace(old_read, new_read)
    print("BACKEND: Added PTY OUT debug print")
else:
    print("BACKEND: WARNING - Could not find read_output block")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
