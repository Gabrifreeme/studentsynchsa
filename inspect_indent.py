import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()
for n in range(15299, 15320):
    print(f"{n+1:5}: |{lines[n].rstrip()}|")
