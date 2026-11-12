import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for n in range(5595, 5665):
    raw = lines[n-1].rstrip("\n").rstrip("\r")
    print(f"{n:5}: |{raw}|")
