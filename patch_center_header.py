import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the header div we just rebuilt (look for justify-content: space-between inside terminal-panel)
header_idx = None
for i, line in enumerate(lines):
    if "display: flex; justify-content: space-between; align-items: center; padding: 4px 8px;" in line:
        header_idx = i
        break

assert header_idx is not None, "Could not find the header div"

# Replace it with a centered version
lines[header_idx] = '  <div style="display: flex; justify-content: center; align-items: center; gap: 15px; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">' + eol

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Centered header at line {header_idx+1}")
