import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the RichText block (around line 235)
rich_start = None
for i, line in enumerate(lines):
    if "? RichText(" in line and "message.text.contains('ACEsi')" in lines[i-1]:
        rich_start = i
        break

assert rich_start is not None, "Could not find RichText block"

# Replace the inner TextSpan child construction (around line 244)
# Current: TextSpan(text: message.text + ' '),
# We need to split on '⭐ ' to insert the RSA star before 'First things first'
for i in range(rich_start, rich_start + 30):
    if "TextSpan(text: message.text + ' ')" in lines[i]:
        # Replace with a split-based construction
        new_lines = (
            "                          ...(message.text.contains('⭐ ')" + eol +
            "                            ? [TextSpan(text: message.text.split('⭐ ')[0]), " + eol +
            "                               WidgetSpan(alignment: PlaceholderAlignment.middle, child: StarAvatar(size: 16))," + eol +
            "                               TextSpan(text: ' ' + message.text.split('⭐ ')[1])]" + eol +
            "                            : [TextSpan(text: message.text + ' ')])," + eol
        )
        lines[i] = new_lines
        print(f"REPLACED: TextSpan at line {i+1} with split-based star injection")
        break
else:
    print("WARNING: Could not find TextSpan(text: message.text + ' ')")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
