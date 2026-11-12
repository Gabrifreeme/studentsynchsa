import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

old_handler = """    socket.on('terminal_output', function(data) {
        term.write(data);
    });"""

new_handler = """    socket.on('terminal_output', function(data) {
        // Detect heartbeat frames and add a green tick
        if (data.match(/\\[SERVER\\]\\s*[\\/_|\\\\]/)) {
            data = data.replace(/\\[SERVER\\](\\s*[\\/_|\\\\])/, '[SERVER]$1 \\x1b[32m\\u2705\\x1b[0m');
        }
        term.write(data);
    });"""

if old_handler in html:
    html = html.replace(old_handler, new_handler)
    print("FRONTEND: Added heartbeat tick detection")
else:
    print("FRONTEND: WARNING - Could not find terminal_output handler")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
