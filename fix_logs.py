import io

# 1. Remove the TerminalLogger hook from server.py
py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

start_marker = "# --- ROUTE STDOUT TO ACEsi TERMINAL ---"
end_marker = "# -------------------------------------"
if start_marker in py:
    start_idx = py.find(start_marker)
    end_idx = py.find(end_marker) + len(end_marker)
    py = py[:start_idx] + py[end_idx:]
    print("BACKEND: Removed TerminalLogger hook")
else:
    print("BACKEND: Hook not found (already removed)")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)

# 2. Update launch.ps1 to redirect output to server.log
launch_path = r"C:\Users\chris\LipSyncStudent\launch.ps1"
with io.open(launch_path, "r", encoding="utf-8", newline="") as f:
    launch = f.read()

old_launch = "Start-Process powershell -ArgumentList '-WindowStyle', 'Hidden', '-Command', 'cd C:\\Users\\chris\\LipSyncStudent; python server.py'"
new_launch = "Start-Process powershell -ArgumentList '-WindowStyle', 'Hidden', '-Command', 'cd C:\\Users\\chris\\LipSyncStudent; python server.py *> server.log'"

if old_launch in launch:
    launch = launch.replace(old_launch, new_launch)
    print("LAUNCH: Redirected server output to server.log")
else:
    # Fallback for lowercase
    launch = launch.replace("python server.py", "python server.py *> server.log")
    print("LAUNCH: Applied fallback log redirection")

with io.open(launch_path, "w", encoding="utf-8", newline="") as f:
    f.write(launch)

print("PATCH COMPLETE")
