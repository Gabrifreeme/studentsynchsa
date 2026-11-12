import io

py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Replace the entire terminal_resize handler to be bulletproof
old_resize_block = """@socketio.on('terminal_resize')
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
                pass"""

new_resize_block = """@socketio.on('terminal_resize')
def handle_terminal_resize(data):
    global terminal_process
    if terminal_process and terminal_process.isalive():
        try:
            # pywinpty on Windows expects (rows, cols) as integers
            r = int(data.get('rows', 24))
            c = int(data.get('cols', 80))
            print(f"RESIZING PTY TO: {r} rows, {c} cols")
            terminal_process.setwinsize(r, c)
        except Exception as e:
            print(f"RESIZE ERROR: {e}")"""

if old_resize_block in py:
    py = py.replace(old_resize_block, new_resize_block)
    print("BACKEND: Fixed terminal_resize handler arguments and added debug logging")
else:
    # Fallback if whitespace didn't match perfectly
    import re
    py = re.sub(
        r"@socketio\.on\('terminal_resize'\)\ndef handle_terminal_resize\(data\):.*?pass",
        new_resize_block,
        py,
        flags=re.DOTALL
    )
    print("BACKEND: Fixed terminal_resize via regex fallback")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
