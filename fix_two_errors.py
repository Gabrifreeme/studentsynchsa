import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# 1. Add url_launcher import
if "package:url_launcher/url_launcher.dart" not in content:
    content = content.replace(
        "import 'package:uuid/uuid.dart';",
        "import 'package:url_launcher/url_launcher.dart';\r\nimport 'package:uuid/uuid.dart';",
        1
    )
    print("ADDED: url_launcher import")

# 2. Fix file.bytes -> await file.xFile.readAsBytes()
if "final bytes = file.bytes;" in content:
    content = content.replace(
        "final bytes = file.bytes;",
        "final bytes = await file.xFile.readAsBytes();"
    )
    print("FIXED: file.bytes -> await file.xFile.readAsBytes()")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE")
