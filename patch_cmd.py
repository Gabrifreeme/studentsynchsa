import io

# 1. FRONTEND: Force the JS to set the height to 280px via inline style
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "setTimeout(function() {" in line and "screen" in lines[i+1]:
        # Inject height lock inside the JS lock we added
        if "termContainer.style.height = '280px';" not in line:
            lines.insert(i + 1, "        termContainer.style.height = '280px';\n        termContainer.style.minHeight = '280px';\n")
            print(f"FRONTEND: Injected height lock at line {i+2}")
            break

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

# 2. BACKEND: Spawn cmd.exe
py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

py = py.replace(
    "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile')",
    "terminal_process = PtyProcess.spawn('cmd.exe')"
)

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("BACKEND: Swapped spawn to cmd.exe")

print("PATCH COMPLETE")
