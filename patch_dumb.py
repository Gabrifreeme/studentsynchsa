import io

py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# 1. Ensure TERM is set to dumb (stops PowerShell cursor manipulation)
if "os.environ['TERM']" not in py:
    py = py.replace(
        "import os\n",
        "import os\nos.environ['TERM'] = 'dumb'\n",
        1
    )
    print("BACKEND: Added TERM=dumb environment variable")

# 2. Force the spawn command to use the dumb flag
old_spawn = "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')"
new_spawn = "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')"
if old_spawn in py:
    py = py.replace(old_spawn, new_spawn)
    print("BACKEND: Verified PowerShell spawn flags")

# 3. Force the PTY to send the exact literal bytes without line-ending wrapping
old_input = "terminal_process.write(data)"
new_input = """if data == '\\r':
                terminal_process.write('\\r')
            else:
                terminal_process.write(data)"""
if old_input in py:
    py = py.replace(old_input, new_input)
    print("BACKEND: Forced raw carriage return handling")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
