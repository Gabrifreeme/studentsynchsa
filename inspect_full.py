import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()
print("=== runTerminalCommand body (2685-2725) ===")
for n in range(2685, 2726):
    raw = lines[n-1].rstrip("\n").rstrip("\r")
    print(f"{n:5}: |{raw}|")
print()
print("=== auto-run checks caller (3345-3365) ===")
for n in range(3345, 3366):
    raw = lines[n-1].rstrip("\n").rstrip("\r")
    print(f"{n:5}: |{raw}|")
print()
print("=== DOMContentLoaded terminal block (5135-5175) ===")
for n in range(5135, 5176):
    raw = lines[n-1].rstrip("\n").rstrip("\r")
    print(f"{n:5}: |{raw}|")
