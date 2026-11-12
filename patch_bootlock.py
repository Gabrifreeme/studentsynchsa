import io

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Add a boot lock variable
if "window.__aceTermBooting" not in html:
    html = html.replace(
        "window.initAceTerminal = function() {",
        "window.initAceTerminal = function() {\n    window.__aceTermBooting = true;"
    )

# 2. Unlock it in the connect handler
if "window.__aceTermBooting = false;" not in html:
    html = html.replace(
        "socket.on('connect', function() {",
        "socket.on('connect', function() {\n        window.__aceTermBooting = false;"
    )

# 3. Block input while booting
old_ondata = """    term.onData(function(data) {
        console.log("xterm sent:", JSON.stringify(data));
        socket.emit('terminal_input', data);
    });"""

new_ondata = """    term.onData(function(data) {
        if (window.__aceTermBooting) {
            // Ignore keystrokes while PTY is booting
            return;
        }
        socket.emit('terminal_input', data);
    });"""

if old_ondata in html:
    html = html.replace(old_ondata, new_ondata)
    print("FRONTEND: Added boot lock to term.onData")
elif "term.onData(function(data) {" in html:
    # Fallback if the console.log was already removed
    html = html.replace(
        "term.onData(function(data) {",
        "term.onData(function(data) {\n        if (window.__aceTermBooting) { return; }"
    )
    print("FRONTEND: Added boot lock to term.onData (fallback)")

# 4. Ensure the initial resize happens AFTER the unlock
# Find where we removed the setTimeout and add it back correctly inside openAceTerminal
if "socket.emit('terminal_resize', dims);" in html:
    # Add a timeout to delay the resize emit until after the fit
    html = html.replace(
        "socket.emit('terminal_resize', dims);",
        "setTimeout(function(){ socket.emit('terminal_resize', dims); }, 300);"
    )

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
