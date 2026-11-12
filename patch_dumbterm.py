import io

py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# 1. Spawn PowerShell with -NonInteractive and set the TERM env variable
old_spawn = "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile')"
new_spawn = """os.environ['TERM'] = 'xterm-256color'
        terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')"""

if old_spawn in py:
    py = py.replace(old_spawn, new_spawn)
    print("BACKEND: Spawned PowerShell in NonInteractive mode with xterm-256color")
else:
    print("BACKEND: WARNING - Could not find spawn line")

# 2. Ensure we are sending the exact raw bytes (no double encoding)
old_input = """        try:
            # Write data directly. If it's a newline, ensure it's \\r
            if data == '\\r' or data == '\\r\\n':
                terminal_process.write('\\r\\n')
            else:
                terminal_process.write(data)
        except Exception:
            pass"""

new_input = """        try:
            terminal_process.write(data)
        except Exception:
            pass"""

if old_input in py:
    py = py.replace(old_input, new_input)
    print("BACKEND: Cleaned up terminal_input write")
else:
    print("BACKEND: Input write block already clean")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
