import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Verify (0-indexed 2057-2058 -> 1-indexed 2058-2059)
assert lines[2057].strip() == '"', f"L2058 mismatch: {lines[2057]!r}"
assert lines[2058].strip() == '"', f"L2059 mismatch: {lines[2058]!r}"
assert "openAceTerminal" in lines[2056], f"L2057 mismatch: {lines[2056]!r}"

# Delete the two orphan quote lines
new_lines = lines[:2057] + lines[2059:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Deleted orphan quotes at lines 2058-2059")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
