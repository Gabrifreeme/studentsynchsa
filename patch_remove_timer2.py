import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Verify the exact lines (1-indexed -> 0-indexed)
assert "setTimeout(function() { window._blockOutput = false; }, 2000);" in lines[11373], f"L11374 mismatch: {lines[11373]!r}"
assert lines[11381].count("window._blockOutput = false;") == 1 and lines[11380].count("window._blockOutput = false;") == 1, "Duplicate false check not found"

# Delete line 11374 (the timer) FIRST - index 11373
del lines[11373]
# After deletion, line 11382 (originally) is now line 11381 (0-indexed 11380)
assert "window._blockOutput = false;" in lines[11380], f"After shift, L11381 mismatch: {lines[11380]!r}"
del lines[11380]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE: Removed 2-second timer + duplicate false")
