import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Swap star position in AppBar (line 119 -> 0-indexed 118)
assert "StarAvatar(size: 28)" in lines[118] and "Text('ACEsi')" in lines[118], f"L119 mismatch: {lines[118]!r}"
lines[118] = "            children: [Text('ACEsi'), SizedBox(width: 8), StarAvatar(size: 28)]," + eol
print("FIXED: AppBar - star now after ACEsi at line 119")

# 2. Add small star at start of "First things first" in the actual greeting (line 48 -> 0-indexed 47)
assert "First things first" in lines[47] and "⭐" not in lines[47], f"L48 mismatch: {lines[47]!r}"
lines[47] = lines[47].replace('"First things first', '"⭐ First things first')
print("ADDED: star before 'First things first' at line 48")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
