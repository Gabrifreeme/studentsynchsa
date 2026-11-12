import io
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
py_path = r"C:\Users\chris\LipSyncStudent\server.py"

# --- FRONTEND: Preserve History ---
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Update openAceTerminal to NOT destroy the terminal
old_open = """    if (window.term) {
        try { window.term.dispose(); } catch(e) {}
        window.term = null;
    }"""
new_open = """    // DO NOT dispose terminal, just show it"""
html = html.replace(old_open, new_open)

# 2. Update closeAceTerminal to just hide the panel
old_close = """        p.style.setProperty('display', 'none', 'important');
        p.setAttribute('hidden', 'true');"""
new_close = """        p.style.setProperty('display', 'none', 'important');
        p.setAttribute('hidden', 'true');
        if (window.term) { window.term.blur(); }"""
html = html.replace(old_close, new_close)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Preserved terminal history on open/close")


# --- BACKEND: Fix Heartbeat Carriage Return ---
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Find the TerminalLogger write method and fix the carriage return
old_write = """    def write(self, msg):
        if msg.strip():
            try:
                clean = msg.replace('\\r', '').replace('\\n', '\\r\\n')
                socketio.emit('terminal_output', '\\r\\n\\x1b[33m[SERVER] ' + clean + '\\x1b[0m')
            except Exception:
                pass
        return super().write(msg)"""

new_write = """    def write(self, msg):
        if msg.strip():
            try:
                # If the message has a carriage return, use it to overwrite the line
                if '\\r' in msg:
                    clean = msg.replace('\\n', '\\r\\n')
                    # Just emit the raw carriage return and the text
                    socketio.emit('terminal_output', clean)
                else:
                    clean = msg.replace('\\n', '\\r\\n')
                    socketio.emit('terminal_output', '\\x1b[33m[SERVER] ' + clean + '\\x1b[0m')
            except Exception:
                pass
        return super().write(msg)"""

if old_write in py:
    py = py.replace(old_write, new_write)
    print("BACKEND: Fixed heartbeat to overwrite line instead of newline")
else:
    print("BACKEND: WARNING - Could not find write method")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
