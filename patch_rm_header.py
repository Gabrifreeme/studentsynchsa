import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the header div (line 7279)
header_idx = None
for i, line in enumerate(lines):
    if "display: flex !important; flex-direction: row !important; align-items: center !important; justify-content: center !important; padding: 4px 8px; background: #111;" in line:
        header_idx = i
        break

assert header_idx is not None, "Could not find the header div"

# Find the closing </div> of the header (usually 6 lines down)
header_end = header_idx + 6
assert "</div>" in lines[header_end], f"Could not find header close at line {header_end+1}"

# Delete the header block
new_lines = lines[:header_idx] + lines[header_end + 1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Deleted terminal header (lines {header_idx+1} to {header_end+1})")
