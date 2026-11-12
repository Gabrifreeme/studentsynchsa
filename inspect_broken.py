import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
print("=== Top (5570-5600) ===")
for n in range(5570, 5600):
    print(f"{n+1:5}: |{lines[n].rstrip()}|")
print()
print("=== Bottom (5690-5730) ===")
for n in range(5690, min(len(lines), 5730)):
    print(f"{n+1:5}: |{lines[n].rstrip()}|")
