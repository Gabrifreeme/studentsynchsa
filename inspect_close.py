import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
# Find where initAceTerminalFn ends
for i, line in enumerate(lines):
    if "window.addEventListener('resize', function() {" in line and i > 5600:
        for n in range(i, min(len(lines), i + 20)):
            print(f"{n+1:5}: |{lines[n].rstrip()}|")
        break
