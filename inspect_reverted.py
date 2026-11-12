import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find where initAceTerminal starts and print 80 lines from there
for i, line in enumerate(lines):
    if "new Terminal({" in line:
        for n in range(i - 10, min(len(lines), i + 70)):
            print(f"{n+1:5}: |{lines[n].rstrip()}|")
        break
