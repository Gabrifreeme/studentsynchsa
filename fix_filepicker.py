import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

content = content.replace("FilePicker.platform.pickFiles()", "FilePicker.pickFiles()")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("FIXED: FilePicker.platform -> FilePicker")
