import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Insert mainAxisAlignment: center right after mainAxisSize line (line 118 -> 0-indexed 117)
assert "mainAxisSize: MainAxisSize.min," in lines[117], f"L118 mismatch: {lines[117]!r}"
lines.insert(118, "            mainAxisAlignment: MainAxisAlignment.center," + eol)
print("FIXED: Added mainAxisAlignment center to AppBar row")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
