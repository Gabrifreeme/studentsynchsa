import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the AppBar( line and insert centerTitle: true right after it
for i, line in enumerate(lines):
    if "appBar: AppBar(" in line:
        lines.insert(i + 1, "          centerTitle: true," + eol)
        print(f"FIXED: Added centerTitle to AppBar at line {i+2}")
        break
else:
    print("WARNING: Could not find AppBar")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
