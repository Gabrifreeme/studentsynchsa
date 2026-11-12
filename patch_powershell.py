import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the spawn line
for i, line in enumerate(lines):
    if "PtyProcess.spawn('cmd.exe')" in line:
        lines[i] = line.replace("PtyProcess.spawn('cmd.exe')", "PtyProcess.spawn('powershell.exe -NoLogo -NoProfile')")
        print(f"BACKEND: Swapped cmd.exe to powershell.exe at line {i+1}")
        break

# Remove the aggressive CR strip we just added (PowerShell handles it properly)
for i, line in enumerate(lines):
    if "clean_data = clean_data.replace('\\r\\n', '\\n').replace('\\r', '')" in line:
        lines[i] = ""
        print(f"BACKEND: Removed CR strip at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
