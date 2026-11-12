import io, re
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# 1. Remove the disconnect handler so the PTY survives socket disconnects
py = re.sub(r"@socketio\.on\('disconnect'\)\ndef handle_disconnect\(\):.*?(?=@socketio|\Z)", "", py, flags=re.DOTALL)
print("BACKEND: Removed disconnect kill handler")

# 2. Fix handle_connect to reuse existing PTY
old_connect = """@socketio.on('connect')
def handle_connect():
    global terminal_process
    # Kill old PTY if any (prevents ghost buffers on reopen)
    if terminal_process:
        try:
            terminal_process.terminate(force=True)
        except Exception:
            pass
        terminal_process = None
    # Spawn fresh PowerShell
    os.environ['TERM'] = 'xterm-256color'
    terminal_process = PtyProcess.spawn('cmd.exe')"""

new_connect = """@socketio.on('connect')
def handle_connect():
    global terminal_process
    # Reuse existing PTY if it's alive (allows running server.py inside ACEsi)
    if terminal_process and terminal_process.isalive():
        print("PTY REATTACHED (already running)")
        return
    # Spawn fresh shell only if none exists
    os.environ['TERM'] = 'xterm-256color'
    terminal_process = PtyProcess.spawn('cmd.exe')"""

if old_connect in py:
    py = py.replace(old_connect, new_connect)
    print("BACKEND: handle_connect now reuses existing PTY")
else:
    # Fallback - simple replacement of the kill block
    py = py.replace(
        "    # Kill old PTY if any (prevents ghost buffers on reopen)\n    if terminal_process:\n        try:\n            terminal_process.terminate(force=True)\n        except Exception:\n            pass\n        terminal_process = None\n    # Spawn fresh PowerShell",
        "    # Reuse existing PTY if alive\n    if terminal_process and terminal_process.isalive():\n        print('PTY REATTACHED')\n        return\n    # Spawn fresh shell"
    )
    print("BACKEND: handle_connect fallback applied")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
