import io, re
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
py_path = r"C:\Users\chris\LipSyncStudent\server.py"

with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

html = html.replace("        console.log('RAW IN:', JSON.stringify(data));\r\n", "")
html = html.replace("        console.log('RAW IN:', JSON.stringify(data));\n", "")
html = html.replace("        console.log('RAW IN:', JSON.stringify(data));", "")

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Removed RAW IN debug log")

with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

old_write = """    def write(self, msg):
        if msg.strip():
            try:
                socketio.emit('terminal_output', '\\r\\n\\x1b[33m[SERVER] ' + msg.replace('\\n', '\\r\\n') + '\\x1b[0m')
            except Exception:
                pass
        return super().write(msg)"""

new_write = """    def write(self, msg):
        if msg.strip():
            try:
                clean = msg.replace('\\r', '').replace('\\n', '\\r\\n')
                socketio.emit('terminal_output', '\\r\\n\\x1b[33m[SERVER] ' + clean + '\\x1b[0m')
            except Exception:
                pass
        return super().write(msg)"""

if old_write in py:
    py = py.replace(old_write, new_write)
    print("BACKEND: Stripped CR from [SERVER] output")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
