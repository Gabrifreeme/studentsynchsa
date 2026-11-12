import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Update the Ctrl+C handler in term.onData to disable auto-scroll
old_ctrlc = """        if (data === '\\x03') {
            socket.emit('terminal_input', '\\x03');
            term.write('^C\\r\\n');
            window._aceBuf = '';
            return;
        }"""

new_ctrlc = """        if (data === '\\x03') {
            socket.emit('terminal_input', '\\x03');
            term.write('^C\\r\\n');
            window._aceBuf = '';
            if (window.term) { window.term.options.scrollback = 0; }
            return;
        }"""

if old_ctrlc in html:
    html = html.replace(old_ctrlc, new_ctrlc)
    print("JS: Ctrl+C now disables auto-scroll")
else:
    print("WARNING: Could not find Ctrl+C block")

# 2. Re-enable auto-scroll when pressing Enter
old_enter = """        if (data === '\\r') {
            if (window._aceBuf.length > 0) {
                socket.emit('terminal_input', window._aceBuf);
                window._aceBuf = '';
            }
        }"""

new_enter = """        if (data === '\\r') {
            if (window.term) { window.term.options.scrollback = 2000; }
            if (window._aceBuf.length > 0) {
                socket.emit('terminal_input', window._aceBuf);
                window._aceBuf = '';
            }
        }"""

if old_enter in html:
    html = html.replace(old_enter, new_enter)
    print("JS: Enter now re-enables auto-scroll")
else:
    print("WARNING: Could not find Enter block")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
