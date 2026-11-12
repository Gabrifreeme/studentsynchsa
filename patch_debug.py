import io

# --- FIX FRONTEND ---
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Nuke the absolute positioning hacks we added earlier and replace with pure flex reset
old_css = """
/* FORCE XTERM TO TOP LEFT */
.xterm { position: absolute !important; top: 0 !important; left: 0 !important; text-align: left !important; }
.xterm-viewport { position: absolute !important; top: 0 !important; left: 0 !important; }
.xterm-screen { position: absolute !important; top: 0 !important; left: 0 !important; text-align: left !important; }
"""
new_css = """
/* XTERM LAYOUT FIX */
#terminal-output { display: block !important; padding: 0 !important; margin: 0 !important; text-align: left !important; }
.xterm { padding: 0 !important; margin: 0 !important; text-align: left !important; }
.xterm-screen { text-align: left !important; }
"""
if old_css in html:
    html = html.replace(old_css, new_css)
    print("FRONTEND: Cleaned up xterm CSS hacks")
else:
    print("FRONTEND: WARNING - old CSS hacks not found")

# 2. Remove the padding JS injection that pushes text around
html = html.replace("termContainer.style.padding = '4px';", "termContainer.style.padding = '0px';")

# 3. Ensure convertEol is set
if "convertEol: true" not in html:
    html = html.replace("cursorBlink: true,", "cursorBlink: true,\n        convertEol: true,")
    print("FRONTEND: Added convertEol: true to xterm config")

# 4. Add debug logging to the onData hook
old_ondata = """    // Send keystrokes to backend
    term.onData(function(data) {
        socket.emit('terminal_input', data);
    });"""
new_ondata = """    // Send keystrokes to backend
    term.onData(function(data) {
        console.log("xterm sent:", JSON.stringify(data));
        socket.emit('terminal_input', data);
    });"""
if old_ondata in html:
    html = html.replace(old_ondata, new_ondata)
    print("FRONTEND: Added debug logging to term.onData")

with io.open(html_path, "w", encoding="utf-8") as f:
    f.write(html)


# --- FIX BACKEND ---
py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8") as f:
    py = f.read()

# Remove the explicit '\r' block we tried earlier, it might be confusing pywinpty
old_backend = """        try:
            # If data is a carriage return, ensure it is strictly '\\r'
            if data == '\\r':
                terminal_process.write('\\r')
            else:
                terminal_process.write(data)
        except Exception:
            pass"""
new_backend = """        try:
            print(f"PTY received: {repr(data)}") # Debug print in terminal
            terminal_process.write(data)
        except Exception:
            pass"""

if old_backend in py:
    py = py.replace(old_backend, new_backend)
    print("BACKEND: Removed forced \\r handler, added debug print")
else:
    print("BACKEND: WARNING - Could not find backend input block")

with io.open(py_path, "w", encoding="utf-8") as f:
    f.write(py)
print("PATCH COMPLETE")
