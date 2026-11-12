import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the socket.connect block in the terminal init
old_connect = """    socket.on('connect', function() {
        term.writeln('\\x1b[33mACEsi Terminal connected.\\x1b[0m');
        var dims = { rows: term.rows, cols: term.cols };
        socket.emit('terminal_resize', dims);
    });"""

new_connect = """    socket.on('connect', function() {
        var dims = { rows: term.rows, cols: term.cols };
        socket.emit('terminal_resize', dims);
        // Auto-tail the server log in the terminal
        setTimeout(function() {
            socket.emit('terminal_input', 'Get-Content server.log -Wait -Tail 20\\r');
        }, 800);
    });"""

if old_connect in html:
    html = html.replace(old_connect, new_connect)
    print("FRONTEND: Auto-tail command injected into socket.connect")
else:
    print("FRONTEND: WARNING - Could not find exact socket.connect block")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
