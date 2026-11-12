import io
path = r"C:\Users\chris\LipSyncStudent\lib\main.dart"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Add kIsWeb import if not present
import_line = "import 'package:flutter/foundation.dart';" + eol
if "package:flutter/foundation.dart" not in "".join(lines):
    lines.insert(2, import_line)  # after flutter/services
    print("IMPORT: Added flutter/foundation.dart")

# 2. Guard the setWebContentsDebuggingEnabled call
for i, line in enumerate(lines):
    if "await InAppWebViewController.setWebContentsDebuggingEnabled(true);" in line:
        # Replace with guarded version
        indent = line[:len(line) - len(line.lstrip())]
        new_lines = (
            indent + "// Only set WebView debugging on mobile platforms" + eol +
            indent + "if (!kIsWeb) {" + eol +
            indent + "  await InAppWebViewController.setWebContentsDebuggingEnabled(true);" + eol +
            indent + "}" + eol
        )
        lines[i] = new_lines
        print(f"FIXED: Guarded setWebContentsDebuggingEnabled at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE")
