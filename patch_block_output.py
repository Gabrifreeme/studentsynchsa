import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Update term.onData: Ctrl+C sets a block flag
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
            window._blockOutput = true;
            return;
        }"""

if old_ctrlc in html:
    html = html.replace(old_ctrlc, new_ctrlc)
    print("JS: Ctrl+C now sets _blockOutput flag")
else:
    print("WARNING: Could not find Ctrl+C block")

# 2. Update Enter: clears the flag
old_enter = """        if (data === '\\r') {
            if (window._aceBuf.length > 0) {
                socket.emit('terminal_input', window._aceBuf);
                window._aceBuf = '';
            }
        }"""

new_enter = """        if (data === '\\r') {
            window._blockOutput = false;
            if (window._aceBuf.length > 0) {
                socket.emit('terminal_input', window._aceBuf);
                window._aceBuf = '';
            }
        }"""

if old_enter in html:
    html = html.replace(old_enter, new_enter)
    print("JS: Enter now clears _blockOutput flag")
else:
    print("WARNING: Could not find Enter block")

# 3. Update terminal_output handler: ignore data if flag is set
old_output = """    socket.on('terminal_output', function(data) {
        // Detect heartbeat frames and add a green tick
        if (/\\[SERVER\\]\\s*[\\/_|\\\\]/.test(data)) {
            data = data.replace(/(\\[SERVER\\]\\s*[\\/_|\\\\])/, '$1 \\x1b[32m\\u2705\\x1b[0m');
        }
        term.write(data);
    });"""

new_output = """    socket.on('terminal_output', function(data) {
        if (window._blockOutput) { return; }
        // Detect heartbeat frames and add a green tick
        if (/\\[SERVER\\]\\s*[\\/_|\\\\]/.test(data)) {
            data = data.replace(/(\\[SERVER\\]\\s*[\\/_|\\\\])/, '$1 \\x1b[32m\\u2705\\x1b[0m');
        }
        term.write(data);
    });"""

if old_output in html:
    html = html.replace(old_output, new_output)
    print("JS: terminal_output now checks _blockOutput flag")
else:
    print("WARNING: Could not find terminal_output handler")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
