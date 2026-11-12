import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\universities\university_webview_screen.dart"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

eol = "\r\n" if "\r\n" in content else "\n"

# 1. Add foundation import if not present
if "package:flutter/foundation.dart" not in content:
    content = content.replace(
        "import 'package:flutter/material.dart';",
        "import 'package:flutter/material.dart';" + eol + "import 'package:flutter/foundation.dart';",
        1
    )
    print("IMPORT: Added flutter/foundation.dart")

# 2. Wrap initState WebView setup with !kIsWeb guard
# Find "    _controller = WebViewController();" and wrap the block
# that starts there until the end of initState setup
if "_controller = WebViewController();" in content and "if (!kIsWeb) {" not in content.split("_controller = WebViewController();")[0][-200:]:
    # Wrap the whole WebView setup. Insert `if (!kIsWeb) {` before controller creation,
    # and `}` before the closing of initState. But it's tricky because _controller is late.
    #
    # Better: just guard the controller creation itself, so _controller stays null on web
    # and build() short-circuits. But _controller is `late` so we'd need to guard every use.
    #
    # Simplest safe approach: replace _controller = WebViewController(); with a guard
    # and use a nullable _controller.
    pass

print("Check complete")
