import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Verify the script didn't eat the xterm HTML tag
if "<div class=\"xterm\">" in html or "class=\"xterm\"" in html:
    print("HTML: xterm div is present")
else:
    print("HTML: WARNING - xterm div may be missing, checking...")

# 2. Add height to the #terminal-output container (the parent)
old_css = "#terminal-output {"
new_css = "#terminal-output { height: 280px !important; min-height: 280px !important; "
if old_css in html:
    html = html.replace(old_css, new_css)
    print("CSS: Added height to #terminal-output")

# 3. Add height to .xterm-viewport
old_viewport = ".xterm-viewport {"
new_viewport = ".xterm-viewport { height: 280px !important; "
if old_viewport in html:
    html = html.replace(old_viewport, new_viewport)
    print("CSS: Added height to .xterm-viewport")

# 4. If .xterm-viewport doesn't exist as a CSS rule, append it
if ".xterm-viewport {" not in html:
    html = html.replace("</style>", ".xterm-viewport { height: 280px !important; overflow-y: scroll !important; }\n</style>", 1)
    print("CSS: Injected fresh .xterm-viewport rule")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("PATCH COMPLETE")
