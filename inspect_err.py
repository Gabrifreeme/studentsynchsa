import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for n in range(5610, 5630):
    print(f"{n+1:5}: |{lines[n].rstrip()}|")
