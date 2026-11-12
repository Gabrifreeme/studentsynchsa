import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. REMOVE the big star on the left of the message
# Find the line with StarAvatar(size: 28) inside the message row (around line 217)
# We do a safe replace: find the specific widget block and comment it out
for i, line in enumerate(lines):
    if "const StarAvatar(size: 28)," in line:
        lines[i] = "            const SizedBox(width: 0), // removed left star\n"
        print(f"REMOVED: left star at line {i+1}")
        break

# 2. ADD star next to 'ACEsi' in the AppBar
# Find: children: [StarAvatar(size: 28), SizedBox(width: 8), Text('ACEsi')],
for i, line in enumerate(lines):
    if "Text('ACEsi')" in line and "StarAvatar" not in line:
        lines[i] = "            children: [Text('ACEsi'), SizedBox(width: 8), StarAvatar(size: 20)],\n"
        print(f"ADDED: star next to ACEsi in AppBar at line {i+1}")
        break

# 3. ADD small star at the start of 'First things first...'
for i, line in enumerate(lines):
    if '"First things first' in line:
        # Replace the starting quote with a star prefix
        lines[i] = line.replace('"First things first', '"⭐ First things first')
        print(f"ADDED: small star before 'First things first' at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
