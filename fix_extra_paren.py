import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Line 262 (1-indexed -> 0-indexed 261) has the extra `),`
assert lines[261].strip() == "),", f"L262 mismatch: {lines[261]!r}"
assert lines[260].strip() == "),", f"L261 mismatch: {lines[260]!r}"

# Delete the extra `),` at line 262
del lines[261]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("SPLICE OK: removed extra `),` at line 262")
