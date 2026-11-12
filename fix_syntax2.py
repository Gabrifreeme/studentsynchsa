import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Sanity check
assert lines[5618].rstrip().endswith("});"), f"L5619 mismatch: {lines[5618]!r}"
assert "ResizeObserver" in lines[5621], f"L5622 mismatch: {lines[5621]!r}"
assert "ResizeObserver" in lines[5630], f"L5631 mismatch: {lines[5630]!r}"
assert "socket.on('disconnect'" in lines[5638], f"L5639 mismatch: {lines[5638]!r}"
assert lines[5653].strip() == "});", f"L5654 mismatch: {lines[5653]!r}"

# Delete lines 5619-5638 (0-indexed 5618-5637)
# That removes: orphan });, dead ResizeObserver #1, dead ResizeObserver #2
new_lines = lines[:5618] + lines[5638:]

# Adjust line 5654 -> 5634 after the deletion (5654 - 20 = 5634, 0-indexed 5633)
# Verify then replace }); with };
assert new_lines[5633].strip() == "});", f"Post-shift L5634 mismatch: {new_lines[5633]!r}"
new_lines[5633] = "};" + eol

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Deleted lines 5619-5638, changed line 5654 to }};")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
