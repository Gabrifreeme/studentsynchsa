import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Sanity check the lines we are about to replace
assert 'onclick="' in lines[2056], f"Line 2057 mismatch: {lines[2056]!r}"
assert 'initAceTerminal' in lines[2057] and 'terminal-panel' in lines[2057], f"Line 2058 mismatch: {lines[2057]!r}"
assert lines[2058].strip() == '"', f"Line 2059 mismatch: {lines[2058]!r}"

# Determine original line ending style from line 2057
eol = "\r\n" if lines[2056].endswith("\r\n") else "\n"

replacement = '        onclick="window.openAceTerminal()"' + eol

# Replace 3 lines (indices 2056..2058) with the single replacement
new_lines = lines[:2056] + [replacement] + lines[2059:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("BUTTON: lines 2057-2059 replaced with onclick=\"window.openAceTerminal()\"")
print(f"Line count before: {len(lines)}, after: {len(new_lines)} (delta {len(new_lines)-len(lines)})")
