import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# 1. Add the disconnect handler to cleanly kill the PTY
disconnect_handler = """
@socketio.on('disconnect')
def handle_disconnect():
    global terminal_process
    if terminal_process:
        try:
            terminal_process.terminate(force=True)
        except Exception:
            pass
        terminal_process = None
    print("SOCKET DISCONNECTED: PTY killed")
"""

# We insert it right before the @socketio.on('connect') handler
if "def handle_disconnect():" not in py:
    py = py.replace("@socketio.on('connect')", disconnect_handler + "\n@socketio.on('connect')")
    print("BACKEND: Added disconnect handler to kill PTY")

# 2. Ensure terminal_process is declared global in the connect handler
if "def handle_connect():\n    global terminal_process" not in py:
    py = py.replace("def handle_connect():", "def handle_connect():\n    global terminal_process")
    print("BACKEND: Ensured global terminal_process in connect")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
