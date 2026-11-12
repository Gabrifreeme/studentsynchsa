import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if "PtyProcess.spawn" in line:
        print(f"{i+1:5}: |{line.rstrip()}|")
