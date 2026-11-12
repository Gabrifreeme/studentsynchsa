import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Verify (1-indexed 5627-5629 -> 0-indexed 5626-5628)
assert "socket.emit('terminal_resize', dims);" in lines[5625], f"L5626 mismatch: {lines[5625]!r}"
assert lines[5626].strip() == "});", f"L5627 mismatch: {lines[5626]!r}"
assert lines[5627].strip() == "});", f"L5628 mismatch: {lines[5627]!r}"
assert "socket.on('terminal_output'" in lines[5629], f"L5630 mismatch: {lines[5629]!r}"

# Delete line 5628 (0-indexed 5627)
new_lines = lines[:5627] + lines[5628:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Deleted orphan }}); at line 5628")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
