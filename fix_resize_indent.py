import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Verify (1-indexed 15291 -> 0-indexed 15290)
assert "BACKEND RESIZE" in lines[15290], f"L15291 mismatch: {lines[15290]!r}"

eol = "\r\n" if lines[15290].endswith("\r\n") else "\n"

# Remove the mis-indented line
del lines[15290]

# Now lines[15290] is the setwinsize line (was 15292, shifted to 15291 -> 0-indexed 15290)
assert "setwinsize(int(data['cols'])" in lines[15290], f"After delete, L15291 mismatch: {lines[15290]!r}"

# Insert properly-indented print BEFORE setwinsize
proper_print = '            print(f\'BACKEND RESIZE: rows={data.get("rows")}, cols={data.get("cols")}\')' + eol
lines.insert(15290, proper_print)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Fixed indentation, print at line 15291")
