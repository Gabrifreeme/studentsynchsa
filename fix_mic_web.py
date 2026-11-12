import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify (1-indexed 135-136 -> 0-indexed 134-135)
assert "Directory.systemTemp" in lines[134], f"L135 mismatch: {lines[134]!r}"
assert "ace_audio_" in lines[135], f"L136 mismatch: {lines[135]!r}"

# Replace with web-safe path logic
new_lines = (
    "          final path = kIsWeb" + eol +
    "              ? 'ace_audio_${DateTime.now().millisecondsSinceEpoch}.m4a'" + eol +
    "              : '${Directory.systemTemp.path}/ace_audio_${DateTime.now().millisecondsSinceEpoch}.m4a';" + eol
)

lines[134:136] = [new_lines]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("SPLICE OK: mic uses web-safe path")
