import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the Text(message.text, ...) block (around line 235)
text_start = None
for i, line in enumerate(lines):
    if "child: Text(" in line and "message.text" in lines[i+1]:
        text_start = i
        break

assert text_start is not None, "Could not find Text(message.text...)"

# Find the closing of the Text block (the next `),` after 10 lines)
text_end = text_start + 1
while text_end < len(lines) and not (lines[text_end].strip() == ")," and ")" in lines[text_end]):
    text_end += 1
# Include one more to close the Text paren properly
text_end += 1

# Verify structure
assert text_end < len(lines), "Could not find end of Text block"

# Replace the Text block with RichText + WidgetSpan
new_block = (
    "              child: (message.text.contains('ACEsi') && !message.isUser)" + eol +
    "                  ? RichText(" + eol +
    "                      text: TextSpan(" + eol +
    "                        style: const TextStyle(" + eol +
    "                          color: AppColors.textPrimary," + eol +
    "                          fontSize: 14," + eol +
    "                          height: 1.5," + eol +
    "                        )," + eol +
    "                        children: [" + eol +
    "                          TextSpan(text: message.text + ' ')," + eol +
    "                          WidgetSpan(" + eol +
    "                            alignment: PlaceholderAlignment.middle," + eol +
    "                            child: StarAvatar(size: 16)," + eol +
    "                          )," + eol +
    "                        ]," + eol +
    "                      )," + eol +
    "                    )" + eol +
    "                  : Text(" + eol +
    "                      message.text," + eol +
    "                      style: const TextStyle(" + eol +
    "                        color: AppColors.textPrimary," + eol +
    "                        fontSize: 14," + eol +
    "                        height: 1.5," + eol +
    "                      )," + eol +
    "                    )," + eol
)

lines[text_start:text_end] = [new_block]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE: RichText + WidgetSpan for inline RSA star")
