import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify (1-indexed 90-91 -> 0-indexed 89-90)
assert "result == null || result.files.isEmpty" in lines[89], f"L90 mismatch: {lines[89]!r}"
assert "result.files.first" in lines[90], f"L91 mismatch: {lines[90]!r}"

# Replace with List<PlatformFile> access
lines[89] = "      if (result.isEmpty) return;" + eol
lines[90] = "      final file = result.first;" + eol

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("FIXED: FilePicker result list access")
