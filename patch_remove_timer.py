import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Remove the 2-second unblock timeout (1-indexed 11374 -> 0-indexed 11373)
assert "setTimeout(function() { window._blockOutput = false; }, 2000);" in lines[11373], f"L11374 mismatch: {lines[11373]!r}"
del lines[11373]
print("REMOVED: 2-second auto-unblock at line 11374")

# Remove the duplicate _blockOutput = true (1-indexed 11377 -> 0-indexed 11376)
assert "window._blockOutput = true;" in lines[11376], f"L11377 mismatch: {lines[11376]!r}"
del lines[11376]
print("REMOVED: Duplicate _blockOutput=true at line 11377")

# Remove the duplicate _blockOutput = false in Enter block (line 11381-11382)
# After removing 2 lines, line 11381 is now 11379, 11382 is now 11380
if "window._blockOutput = false;" in lines[11379] and "window._blockOutput = false;" in lines[11380]:
    del lines[11380]
    print("REMOVED: Duplicate _blockOutput=false in Enter block")

# Remove duplicate _blockOutput check in terminal_output (line 11295-11296)
if "window._blockOutput" in lines[11294] and "window._blockOutput" in lines[11295]:
    del lines[11295]
    print("REMOVED: Duplicate check at line 11296")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE")
