import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find every <script> and </script> tag
for i, line in enumerate(lines):
    s = line.strip().lower()
    if "<script" in s or "</script>" in s:
        print(f"{i+1:5}: |{lines[i].rstrip()}|")
