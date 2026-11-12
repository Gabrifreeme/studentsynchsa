import io, re
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# 1. Replace the connect handler + reader thread with subprocess-based runner
old_connect_pattern = re.compile(
    r"@socketio\.on\('connect'\)\ndef handle_connect\(\):.*?socketio\.start_background_task\(read_output\)",
    re.DOTALL
)

new_connect = """@socketio.on('connect')
def handle_connect():
    print("CLIENT CONNECTED")
    # Each command is a fresh subprocess. No persistent PTY.
"""

py = old_connect_pattern.sub(lambda m: new_connect, py)

# 2. Replace terminal_input handler with subprocess runner
old_input_pattern = re.compile(
    r"@socketio\.on\('terminal_input'\)\ndef handle_terminal_input\(data\):.*?(?=@socketio\.on\('terminal_resize'\))",
    re.DOTALL
)

new_input = """@socketio.on('terminal_input')
def handle_terminal_input(data):
    import subprocess
    import os
    import re as _re
    cmd = data.strip()
    if not cmd:
        return
    prompt = "PS " + os.getcwd() + "> "
    socketio.emit('terminal_output', prompt + cmd + "\\r\\n")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        out = result.stdout + result.stderr
        if out:
            clean = _re.sub(r'\\x1b\\[[0-9;?]*[A-Za-z]', '', out)
            socketio.emit('terminal_output', clean.replace('\\n', '\\r\\n'))
        socketio.emit('terminal_output', "\\r\\n" + prompt)
    except subprocess.TimeoutExpired:
        socketio.emit('terminal_output', "\\r\\n[Timeout]\\r\\n" + prompt)
    except Exception as e:
        socketio.emit('terminal_output', "\\r\\n[Error: " + str(e) + "]\\r\\n" + prompt)

"""

py = old_input_pattern.sub(lambda m: new_input, py)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("BACKEND: Replaced PTY with subprocess runner")
