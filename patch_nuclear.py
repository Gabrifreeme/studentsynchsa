import io, re

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Nuke ALL previous terminal CSS
html = re.sub(r"#terminal-output\s*\{[^}]*\}", "", html)
html = re.sub(r"#terminal-panel\s*\{[^}]*\}", "", html)
html = re.sub(r"\.xterm[^{]*\{[^}]*\}", "", html)

# 2. Inject nuclear CSS
clean_css = """
/* NUCLEAR TERMINAL CSS */
#terminal-panel {
    display: flex !important;
    flex-direction: column !important;
    height: 300px !important;
    min-height: 300px !important;
    max-height: 300px !important;
    position: relative !important;
    background: #000 !important;
    overflow: hidden !important;
}
#terminal-output {
    display: block !important;
    flex: 1 !important;
    height: 280px !important;
    min-height: 280px !important;
    width: 100% !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    background: #000 !important;
    position: relative !important;
}
.xterm {
    width: 100% !important;
    height: 280px !important;
    min-height: 280px !important;
}
.xterm-viewport {
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    width: 100% !important;
    height: 280px !important;
}
.xterm-viewport::-webkit-scrollbar { width: 8px !important; }
.xterm-viewport::-webkit-scrollbar-track { background: #111 !important; }
.xterm-viewport::-webkit-scrollbar-thumb { background: #ff9d00 !important; border-radius: 4px !important; }
"""
html = html.replace("</style>", clean_css + "\n</style>", 1)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Applied nuclear CSS. Terminal forced to 280px height.")
