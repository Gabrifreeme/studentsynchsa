import io, re

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Nuke all old terminal CSS to stop conflicts
html = re.sub(r"#terminal-output\s*\{[^}]*\}", "", html)
html = re.sub(r"#terminal-panel\s*\{[^}]*\}", "", html)
html = re.sub(r"\.xterm[^{]*\{[^}]*\}", "", html)

# 2. Inject the definitive layout and scrollbar CSS
css = """
/* DEFINITIVE TERMINAL & SCROLLBAR CSS */
#terminal-panel {
    display: flex !important;
    flex-direction: column !important;
    height: 300px !important;
    min-height: 300px !important;
    background: #000 !important;
    border-top: 1px solid #ff9d00;
    position: relative !important;
    overflow: hidden !important;
}

#terminal-output {
    flex: 1 !important;
    width: 100% !important;
    height: 100% !important;
    position: relative !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Force xterm to fill the container */
.xterm {
    width: 100% !important;
    height: 100% !important;
    padding: 4px !important;
}

/* Force the scrollbar viewport to be visible and scrollable */
.xterm .xterm-viewport {
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    width: 100% !important;
    background-color: #000 !important;
}

/* Customize the scrollbar appearance */
.xterm-viewport::-webkit-scrollbar {
    width: 10px !important;
}
.xterm-viewport::-webkit-scrollbar-track {
    background: #111 !important;
    border-left: 1px solid #333 !important;
}
.xterm-viewport::-webkit-scrollbar-thumb {
    background: #ff9d00 !important;
    border-radius: 5px !important;
}
"""
html = html.replace("</style>", css + "\n</style>", 1)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)

print("FRONTEND: Nuked old CSS and injected definitive scrollbar CSS.")
