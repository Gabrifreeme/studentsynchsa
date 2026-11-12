import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Verify the button block (1-indexed 2057-2059 -> 0-indexed 2056-2058)
assert 'onclick="' in lines[2056], f"L2057 mismatch: {lines[2056]!r}"
assert "document.getElementById('terminal-panel')" in lines[2057], f"L2058 mismatch: {lines[2057]!r}"
assert lines[2058].strip() == '"', f"L2059 mismatch: {lines[2058]!r}"

eol = "\r\n" if lines[2056].endswith("\r\n") else "\n"

replacement = '        onclick="window.openAceTerminal()"' + eol

new_lines = lines[:2056] + [replacement] + lines[2059:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"BUTTON FIXED: lines 2057-2059 replaced")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
