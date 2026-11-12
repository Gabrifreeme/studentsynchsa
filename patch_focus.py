import io

path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Fix the connect event to delay resize emit
old_connect = """    socket.on('connect', function() {
        term.writeln('\\x1b[33mACEsi Terminal connected.\\x1b[0m');
        var dims = { rows: term.rows, cols: term.cols };
        socket.emit('terminal_resize', dims);
    });"""
new_connect = """    socket.on('connect', function() {
        // Do not write "connected" immediately, let the PTY handle it
        setTimeout(function() {
            var dims = { rows: term.rows, cols: term.cols };
            socket.emit('terminal_resize', dims);
        }, 1000); // Wait 1 second for shell to boot before resizing
    });"""
if old_connect in text:
    text = text.replace(old_connect, new_connect)
    print("SOCKET: Delayed initial resize to prevent PTY corruption")
else:
    print("SOCKET: WARNING - connect block not matched")

# 2. Force focus on click
old_focus = """    // Send keystrokes to backend
    term.onData(function(data) {"""
new_focus = """    // Force focus when clicking anywhere in the terminal
    termContainer.addEventListener('mousedown', function() {
        term.focus();
    });

    // Send keystrokes to backend
    term.onData(function(data) {"""
if old_focus in text:
    text = text.replace(old_focus, new_focus)
    print("FOCUS: Added mousedown focus lock")
else:
    print("FOCUS: WARNING - onData block not matched")

# 3. Refocus after ResizeObserver
old_obs = """            if (window.termFitAddon && termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) {
                try { window.termFitAddon.fit(); } catch(e) {}
            }"""
new_obs = """            if (window.termFitAddon && termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) {
                try { window.termFitAddon.fit(); } catch(e) {}
                if (window.term) { try { window.term.focus(); } catch(e) {} }
            }"""
if old_obs in text:
    text = text.replace(old_obs, new_obs)
    print("OBSERVER: Added focus restore after fit")
else:
    print("OBSERVER: WARNING - resize observer block not matched")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("PATCH COMPLETE")
