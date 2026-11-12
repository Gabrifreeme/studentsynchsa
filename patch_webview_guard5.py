import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\universities\university_webview_screen.dart"
fallback_path = r"C:\Users\chris\LipSyncStudent\fallback_method.txt"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

with io.open(fallback_path, "r", encoding="utf-8", newline="") as f:
    fallback_method = f.read()
    fallback_method = fallback_method.replace("\r\n", "\n").replace("\n", "\r\n" if lines[0].endswith("\r\n") else "\n")

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"
content = "".join(lines)

# 1. ADD IMPORTS FIRST (they'll shift line numbers, so all subsequent finds must be dynamic)
if "flutter/services.dart" not in content:
    for i, line in enumerate(lines):
        if "import 'package:flutter/material.dart';" in line:
            lines.insert(i + 1, "import 'package:flutter/services.dart';" + eol)
            print("ADDED: flutter/services.dart import at line " + str(i+2))
            break

content = "".join(lines)
if "package:url_launcher/url_launcher.dart" not in content:
    for i, line in enumerate(lines):
        if "import 'package:flutter/material.dart';" in line:
            lines.insert(i + 1, "import 'package:url_launcher/url_launcher.dart';" + eol)
            print("ADDED: url_launcher import at line " + str(i+2))
            break

# 2. FIND initState dynamically
initstate_start = None
for i, line in enumerate(lines):
    if "void initState() {" in line:
        initstate_start = i
        print("Found initState at line " + str(i+1))
        break
assert initstate_start is not None, "initState not found"

# Find controller creation
ctrl_idx = None
for i in range(initstate_start, initstate_start + 20):
    if "_controller = WebViewController();" in lines[i]:
        ctrl_idx = i
        print("Found _controller init at line " + str(i+1))
        break
assert ctrl_idx is not None, "WebViewController() creation not found"

# Find @override that ends initState (next @override after initstate_start)
next_override = None
for i in range(initstate_start + 1, len(lines)):
    if lines[i].strip() == "@override":
        next_override = i
        print("Found next @override at line " + str(i+1))
        break
assert next_override is not None, "Could not find end of initState"

# Insert if (!kIsWeb) { before controller creation
lines.insert(ctrl_idx, "    if (!kIsWeb) {" + eol)
print("INSERTED: if (!kIsWeb) { at line " + str(ctrl_idx+1))
# shift next_override by +1
next_override += 1

# Close the block: find the last "}" before next_override
for i in range(next_override - 1, ctrl_idx, -1):
    if lines[i].strip() == "}" and lines[i].startswith("  }"):
        lines.insert(i, "    }" + eol)
        print("INSERTED: closing } at line " + str(i+1))
        break

# 3. FIND build() dynamically
build_idx = None
for i, line in enumerate(lines):
    if "Widget build(BuildContext context) {" in line:
        build_idx = i
        print("Found build() at line " + str(i+1))
        break
assert build_idx is not None, "build() not found"

# 4. Insert kIsWeb guard in build
lines.insert(build_idx + 1, "    if (kIsWeb) { return _buildWebFallback(context); }" + eol)
print("INSERTED: kIsWeb guard at line " + str(build_idx+2))

# 5. Insert fallback method before build
lines.insert(build_idx, fallback_method)
print("INSERTED: _buildWebFallback method at line " + str(build_idx+1))

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
