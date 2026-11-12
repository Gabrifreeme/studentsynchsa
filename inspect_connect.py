import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "@socketio.on('connect')" in line:
        for j in range(i, min(len(lines), i + 40)):
            print(f"{j+1:5}: |{lines[j].rstrip()}|")
        break
