import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Remove any conflicting .xterm CSS
import re
html = re.sub(r"\.xterm[^{]*\{[^}]*\}", "", html)

# Inject the definitive xterm CSS that forces the viewport to have actual height
css = """
/* FIX XTERM VIEWPORT HEIGHT */
.xterm {
    height: 280px !important;
    min-height: 280px !important;
    width: 100% !important;
}
.xterm-screen {
    height: 280px !important;
    min-height: 280px !important;
}
.xterm-viewport {
    height: 280px !important;
    min-height: 280px !important;
    overflow-y: scroll !important;
}
"""
html = html.replace("</style>", css + "\n</style>", 1)

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("PATCH COMPLETE: .xterm and .xterm-viewport forced to 280px")
