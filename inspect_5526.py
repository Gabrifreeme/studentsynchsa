import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for n in range(5525, 5572):
    print(f"{n+1:5}: |{lines[n].rstrip()}|")
