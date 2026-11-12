import io, re
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# 1. Force a raw PowerShell spawn without PSReadLine
old_spawn = "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')"
new_spawn = """os.environ['TERM'] = 'dumb'
        # Disable PSReadLine to stop the floating cursor bug
        ps_cmd = 'powershell.exe -NoLogo -NoProfile -NonInteractive -Command "Remove-Module PSReadLine -ErrorAction SilentlyContinue; Set-PSReadLineOption -EditMode Windows"'
        terminal_process = PtyProcess.spawn(ps_cmd)"""

if old_spawn in py:
    py = py.replace(old_spawn, new_spawn)
    print("BACKEND: Spawned PowerShell with PSReadLine disabled")
else:
    print("BACKEND: WARNING - Could not find spawn line, checking for alternative...")
    # Fallback if the exact string isn't there
    py = py.replace("'powershell.exe -NoLogo -NoProfile -NonInteractive'", "ps_cmd")
    print("BACKEND: Applied fallback spawn replacement")

# 2. Force a 24x80 resize before reading output
old_resize = "terminal_process.setwinsize(24, 80)"
if old_resize not in py:
    py = py.replace(
        "terminal_process = PtyProcess.spawn(ps_cmd)",
        "terminal_process = PtyProcess.spawn(ps_cmd)\n    try: terminal_process.setwinsize(24, 80)\n    except: pass"
    )
    print("BACKEND: Added initial 24x80 resize")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
