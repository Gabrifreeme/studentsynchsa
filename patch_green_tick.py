import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "sys.stdout.write('\\b' + frames[idx])" in line:
        lines[i] = line.replace("sys.stdout.write('\\b' + frames[idx])", "sys.stdout.write('\\b' + frames[idx] + ' \\x1b[32m\\u2705\\x1b[0m')")
        print(f"SPLICE OK: Added green tick to heartbeat at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE")
