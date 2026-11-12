import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\universities\university_webview_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Remove BOM from line 453 (0-indexed 452)
if lines[452].startswith("\ufeff"):
    lines[452] = lines[452][1:]
    print("REMOVED: BOM from line 453")

# 2. Add flutter/foundation.dart import if missing
content = "".join(lines)
if "package:flutter/foundation.dart" not in content:
    for i, line in enumerate(lines):
        if "import 'package:flutter/material.dart';" in line:
            lines.insert(i + 1, "import 'package:flutter/foundation.dart';" + eol)
            print(f"ADDED: flutter/foundation.dart import at line {i+2}")
            break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
