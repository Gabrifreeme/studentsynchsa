import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "terminal-close-btn" in line:
        print(f"{i+1:5}: |{line.rstrip()}|")
