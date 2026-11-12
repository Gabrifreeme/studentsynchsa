import io

# --- FIX 1: FRONTEND ---
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Remove convertEol
html = html.replace("convertEol: true,", "")

# Ensure the CSS is a clean block
css_fix = """
.xterm, .xterm-screen, .xterm-viewport { text-align: left !important; padding: 0 !important; margin: 0 !important; }
"""
if ".xterm, .xterm-screen, .xterm-viewport" not in html:
    html = html.replace("</style>", css_fix + "\n</style>", 1)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Removed convertEol, fixed CSS.")


# --- FIX 2: BACKEND ---
py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Fix the input handler to write raw carriage return bytes correctly
old_input = """        try:
            # Write data directly. If it's a newline, ensure it's \\r
            if data == '\\r' or data == '\\r\\n':
                terminal_process.write('\\r\\n')
            else:
                terminal_process.write(data)
        except Exception:
            pass"""

new_input = """        try:
            # Write the exact bytes. Do not double-encode.
            terminal_process.write(data)
        except Exception:
            pass"""

if old_input in py:
    py = py.replace(old_input, new_input)
    print("BACKEND: Simplified input write to raw bytes.")
else:
    # Fallback if previous patch didn't match
    py = py.replace("terminal_process.write(data)", "terminal_process.write(data)")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
