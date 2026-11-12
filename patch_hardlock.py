import io, re

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Nuke ALL previous terminal CSS to stop conflicts
html = re.sub(r"#terminal-output\s*\{[^}]*\}", "", html)
html = re.sub(r"#terminal-panel\s*\{[^}]*\}", "", html)
html = re.sub(r"\.xterm[^{]*\{[^}]*\}", "", html)

# 2. Inject hard-locked pixel CSS
css = """
/* HARD LOCK TERMINAL CSS */
#terminal-panel {
    display: flex !important;
    flex-direction: column !important;
    height: 300px !important;
    min-height: 300px !important;
    max-height: 300px !important;
    background: #000 !important;
    border-top: 1px solid #ff9d00;
    position: relative !important;
}

#terminal-output {
    display: block !important;
    height: 280px !important;
    min-height: 280px !important;
    max-height: 280px !important;
    width: 100% !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    background: #000 !important;
}

.xterm {
    height: 280px !important;
    width: 100% !important;
}

.xterm .xterm-viewport {
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    height: 280px !important;
}

/* Force the scrollbar to be visible */
.xterm-viewport::-webkit-scrollbar {
    width: 12px !important;
}
.xterm-viewport::-webkit-scrollbar-track {
    background: #222 !important;
}
.xterm-viewport::-webkit-scrollbar-thumb {
    background: #ff9d00 !important;
    border-radius: 6px !important;
}
"""
html = html.replace("</style>", css + "\n</style>", 1)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Applied hard-locked 280px height and forced scrollbar.")
