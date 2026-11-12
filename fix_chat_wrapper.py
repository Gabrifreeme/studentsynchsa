import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify (1-indexed 112-114 -> 0-indexed 111-113)
assert "GradientBackground(" in lines[111], f"L112 mismatch: {lines[111]!r}"
assert "backgroundColor: Colors.transparent" in lines[113], f"L114 mismatch: {lines[113]!r}"

# Replace three lines with plain black Container
lines[111] = "    return Container(" + eol
lines[112] = "      color: Colors.black," + eol
lines[113] = "      child: Scaffold(" + eol
# Insert the Scaffold's backgroundColor line after
lines.insert(114, "        backgroundColor: Colors.black," + eol)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("SPLICE OK: GradientBackground -> Container(black)")
