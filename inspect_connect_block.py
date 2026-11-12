import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "socket.on('connect'" in line:
        for n in range(i, min(len(lines), i + 15)):
            print(f"{n+1:5}: |{lines[n].rstrip()}|")
        break
