import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify (line 10-12 -> 0-indexed 9-11)
assert "return GradientBackground(" in lines[9], f"L10 mismatch: {lines[9]!r}"
assert "child: Scaffold(" in lines[10], f"L11 mismatch: {lines[10]!r}"
assert "backgroundColor: Colors.transparent," in lines[11], f"L12 mismatch: {lines[11]!r}"

# Replace 3 lines with pure black Container
lines[9] = "    return Container(" + eol
lines[10] = "      color: Colors.black," + eol
lines[11] = "      child: Scaffold(" + eol
# Insert the Scaffold's backgroundColor line after
lines.insert(12, "        backgroundColor: Colors.black," + eol)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE: Community Chat - GradientBackground -> black Container")
