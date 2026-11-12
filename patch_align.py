import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

# Remove any existing style tag for terminal-output
html = re.sub(r"#terminal-output\s*\{[^}]*\}", "", html)

# Inject a brutal CSS override right before </head>
css = """
/* FINAL ALIGNMENT FIX */
#terminal-output, #terminal-output *, .xterm, .xterm-screen, .xterm-viewport, .xterm-rows {
    padding-left: 0 !important;
    margin-left: 0 !important;
    text-align: left !important;
    left: 0 !important;
}
#terminal-output {
    display: block !important;
    height: 280px !important;
    width: 100% !important;
    overflow: hidden !important;
    background: #000 !important;
}
.xterm .xterm-viewport {
    overflow-y: scroll !important;
}
"""
html = html.replace("</head>", f"<style>{css}</style>\n</head>", 1)

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("PATCH COMPLETE: Injected final alignment CSS")
