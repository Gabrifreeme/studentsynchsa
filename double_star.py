import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify current line 119 (0-indexed 118)
assert "StarAvatar(size: 28)" in lines[118] and "Text('ACEsi')" in lines[118], f"L119 mismatch: {lines[118]!r}"

# Replace with star on both sides
lines[118] = "            children: [StarAvatar(size: 28), SizedBox(width: 6), Text('ACEsi'), SizedBox(width: 6), StarAvatar(size: 28)]," + eol

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE: AppBar now has RSA star on both sides of ACEsi")
