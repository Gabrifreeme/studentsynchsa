import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Fix line 90 (0-indexed 89): remove withData
for i, line in enumerate(lines):
    if "FilePicker.pickFiles(withData: true)" in line:
        lines[i] = line.replace("FilePicker.pickFiles(withData: true)", "FilePicker.pickFiles()")
        print(f"FIXED: removed withData at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
