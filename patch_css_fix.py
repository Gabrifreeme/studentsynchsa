import io, re

# --- 1. FRONTEND CSS SLEDGEHAMMER ---
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Replace the entire terminal-output CSS block with a strict, left-aligned reset
# We use regex to find the line that starts with #terminal-output { and ends with }
html = re.sub(r"#terminal-output\s*\{[^}]*\}", "#terminal-output { display: block !important; text-align: left !important; padding: 0 !important; margin: 0 !important; width: 100% !important; height: 100% !important; overflow: hidden !important; background: #000 !important; position: relative !important; }", html)

# Force .xterm and all its children to align left
css_inject = """
/* ABSOLUTE FORCE LEFT */
.xterm, .xterm-viewport, .xterm-screen, .xterm-rows { 
    text-align: left !important; 
    margin: 0 !important; 
    padding: 0 !important; 
    left: 0 !important; 
}
.xterm-rows { display: flex !important; flex-direction: column !important; align-items: flex-start !important; }
"""
# Insert it into the head
html = html.replace("</head>", f"<style>{css_inject}</style>\n</head>", 1)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: CSS absolutely forced to left alignment.")


# --- 2. BACKEND PTY RESET ---
py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Spawn PowerShell with -NoLogo so the banner doesn't corrupt the stream
old_spawn = "terminal_process = PtyProcess.spawn('powershell.exe')"
new_spawn = "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile')"

if old_spawn in py:
    py = py.replace(old_spawn, new_spawn)
    print("BACKEND: Changed spawn to '-NoLogo -NoProfile'")
else:
    print("BACKEND: WARNING - Could not find spawn line")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
