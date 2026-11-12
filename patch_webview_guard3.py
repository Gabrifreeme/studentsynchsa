import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\universities\university_webview_screen.dart"
fallback_path = r"C:\Users\chris\LipSyncStudent\fallback_method.txt"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

with io.open(fallback_path, "r", encoding="utf-8", newline="") as f:
    fallback_method = f.read()
    fallback_method = fallback_method.replace("\r\n", "\n").replace("\n", "\r\n" if lines[0].endswith("\r\n") else "\n")

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

assert "void initState() {" in lines[52], f"L53 mismatch: {lines[52]!r}"
assert "_controller = WebViewController();" in lines[59], f"L60 mismatch: {lines[59]!r}"
assert "@override" in lines[174], f"L175 mismatch: {lines[174]!r}"
assert "Widget build(BuildContext context) {" in lines[449], f"L450 mismatch: {lines[449]!r}"

content = "".join(lines)
assert "url_launcher" in content, "url_launcher import missing"
assert "flutter/services.dart" in content, "flutter/services.dart import missing"

lines.insert(59, "    if (!kIsWeb) {" + eol)
print("INSERTED: if (!kIsWeb) { at line 60")

for i in range(176, 60, -1):
    if lines[i].strip() == "}" and lines[i].startswith("  }"):
        lines.insert(i, "    }" + eol)
        print(f"INSERTED: closing }} at line {i+1}")
        break

for i, line in enumerate(lines):
    if "Widget build(BuildContext context) {" in line:
        lines.insert(i + 1, "    if (kIsWeb) { return _buildWebFallback(context); }" + eol)
        print(f"INSERTED: kIsWeb guard at line {i+2}")
        build_idx = i
        break

lines.insert(build_idx, fallback_method)
print(f"INSERTED: _buildWebFallback method at line {build_idx+1}")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
