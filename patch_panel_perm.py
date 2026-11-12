import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

css = """
/* FORCE TERMINAL PANEL HEIGHT - THE REAL FIX */
#terminal-panel {
    height: 300px !important;
    min-height: 300px !important;
    max-height: 300px !important;
    flex: 0 0 300px !important;
}
#terminal-output {
    height: 100% !important;
    min-height: 260px !important;
    flex: 1 1 auto !important;
}
#terminal-output .xterm,
#terminal-output .xterm-viewport,
#terminal-output .xterm-screen {
    height: 100% !important;
    min-height: 260px !important;
}
"""
html = html.replace("</style>", css + "\n</style>", 1)

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("PATCH COMPLETE: panel 300px, viewport fills")
