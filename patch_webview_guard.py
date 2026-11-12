import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\universities\university_webview_screen.dart"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify (1-indexed -> 0-indexed)
assert "void initState() {" in lines[52], f"L53 mismatch: {lines[52]!r}"
assert "_controller = WebViewController();" in lines[59], f"L60 mismatch: {lines[59]!r}"
assert "@override" in lines[174], f"L175 mismatch: {lines[174]!r}"
assert "Widget build(BuildContext context) {" in lines[449], f"L450 mismatch: {lines[449]!r}"

# 1. Insert "if (!kIsWeb) {" before line 60 (_controller = WebViewController())
indent = "    "  # 4 spaces inside initState
lines.insert(59, indent + "if (!kIsWeb) {" + eol)
print("INSERTED: if (!kIsWeb) { at line 60")

# 2. Close the block: insert "    }" before line 175 (which is now line 176 after insert)
# We need to find the closing brace of initState, which is the last line before @override
# Find the line that ends initState (last "}" before line 175+1)
# After insertion at 59, everything shifts +1. The "@override" at 174 is now at 175.
for i in range(174, 60, -1):
    if lines[i].strip() == "}" and lines[i].startswith("  }"):
        # This is the closing of initState
        lines.insert(i, indent + "}" + eol)
        print(f"INSERTED: closing }} at line {i+1}")
        break

# 3. Add kIsWeb guard at start of build()
# Find "Widget build(BuildContext context) {" (now around 451 after two inserts)
for i, line in enumerate(lines):
    if "Widget build(BuildContext context) {" in line:
        # Insert right after the opening brace
        lines.insert(i + 1, "    if (kIsWeb) { return _buildWebFallback(context); }" + eol)
        print(f"INSERTED: kIsWeb guard in build at line {i+2}")
        break

# 4. Add _buildWebFallback method before build()
for i, line in enumerate(lines):
    if "Widget build(BuildContext context) {" in line:
        # Insert method BEFORE the build declaration
        fallback_method = (
            "  Widget _buildWebFallback(BuildContext context) {" + eol +
            "    final url = widget.url;" + eol +
            "    return Scaffold(" + eol +
            "      appBar: AppBar(" + eol +
            "        title: Text(widget.universityName)," + eol +
            "        backgroundColor: Colors.blue," + eol +
            "      )," + eol +
            "      body: Center(" + eol +
            "        child: Padding(" + eol +
            "          padding: const EdgeInsets.all(32.0)," + eol +
            "          child: Column(" + eol +
            "            mainAxisAlignment: MainAxisAlignment.center," + eol +
            "            children: [" + eol +
            "              const Icon(Icons.public, size: 64, color: Colors.blue)," + eol +
            "              const SizedBox(height: 24)," + eol +
            "              Text('Portal: ' + widget.universityName," + eol +
            "                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)," + eol +
            "                textAlign: TextAlign.center)," + eol +
            "              const SizedBox(height: 12)," + eol +
            "              const Text('The WebView does not work in a browser.' + eol +
            "                ' Open the portal in a new Chrome tab and use the" + eol +
            "                ' Autofill button there.'," + eol +
            "                textAlign: TextAlign.center)," + eol +
            "              const SizedBox(height: 24)," + eol +
            "              ElevatedButton.icon(" + eol +
            "                icon: const Icon(Icons.open_in_browser)," + eol +
            "                label: const Text('Open Portal in Chrome')," + eol +
            "                onPressed: () {" + eol +
            "                  final uri = Uri.parse(url);" + eol +
            "                  // ignore: avoid_web_libraries_in_flutter" + eol +
            "                  html.window.open(uri.toString(), '_blank');" + eol +
            "                }," + eol +
            "              )," + eol +
            "              const SizedBox(height: 16)," + eol +
            "              ElevatedButton.icon(" + eol +
            "                icon: const Icon(Icons.copy_all)," + eol +
            "                label: const Text('Copy Autofill Script')," + eol +
            "                onPressed: () async {" + eol +
            "                  final json = _profileJson;" + eol +
            "                  if (json == null || json.isEmpty) {" + eol +
            "                    if (!mounted) return;" + eol +
            "                    ScaffoldMessenger.of(context).showSnackBar(" + eol +
            "                      const SnackBar(content: Text('No profile loaded'), backgroundColor: Colors.orange)," + eol +
            "                    );" + eol +
            "                    return;" + eol +
            "                  }" + eol +
            "                  final script = star.buildAutofillScript(json);" + eol +
            "                  // ignore: avoid_web_libraries_in_flutter" + eol +
            "                  await html.window.navigator.clipboard!.writeText(script);" + eol +
            "                  if (!mounted) return;" + eol +
            "                  // ignore: use_build_context_synchronously" + eol +
            "                  ScaffoldMessenger.of(context).showSnackBar(" + eol +
            "                    const SnackBar(content: Text('Autofill script copied! Paste it in F12 Console on the UFS portal.'), backgroundColor: Colors.green, duration: Duration(seconds: 5))," + eol +
            "                  );" + eol +
            "                }," + eol +
            "              )," + eol +
            "            ]," + eol +
            "          )," + eol +
            "        )," + eol +
            "      )," + eol +
            "    );" + eol +
            "  }" + eol +
            "" + eol
        )
        lines.insert(i, fallback_method)
        print(f"INSERTED: _buildWebFallback method at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
