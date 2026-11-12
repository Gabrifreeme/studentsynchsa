import io, re

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Remove any existing xterm scrollbar CSS to prevent conflicts
html = re.sub(r"\.xterm-viewport\s*\{[^}]*\}", "", html)

# 2. Inject the definitive xterm scrollbar CSS
clean_css = """
/* XTERM SCROLLBAR FIX */
.xterm .xterm-viewport {
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    width: 100% !important;
    height: 100% !important;
    background-color: #000 !important;
}
.xterm-viewport::-webkit-scrollbar {
    width: 8px !important;
}
.xterm-viewport::-webkit-scrollbar-track {
    background: #111 !important;
}
.xterm-viewport::-webkit-scrollbar-thumb {
    background: #ff9d00 !important;
    border-radius: 4px !important;
}
"""
html = html.replace("</style>", clean_css + "\n</style>", 1)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Injected native xterm scrollbar CSS")
