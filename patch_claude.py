import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# --- 1. Inject Claude's CSS right before the last </style> ---
css_block = """
/* CLAUDE FIX: XTERM ANCHOR */
#terminal-output {
    display: block !important;
    text-align: left !important;
    padding: 4px !important;
    box-sizing: border-box;
    position: relative;
    overflow: hidden;
}
#terminal-output .xterm {
    display: block !important;
    position: relative !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: left !important;
}
#terminal-output .xterm-viewport,
#terminal-output .xterm-screen {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: left !important;
}
#terminal-output .xterm-screen canvas {
    display: block !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    margin: 0 !important;
}
#terminal-output .xterm-rows {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    text-align: left !important;
    margin: 0 !important;
}
"""
css_injected = False
for i in range(len(lines) - 1, -1, -1):
    if "</style>" in lines[i]:
        lines[i] = css_block + eol + lines[i]
        css_injected = True
        print(f"CSS: Injected Claude anchor rules before </style> at line {i+1}")
        break
assert css_injected, "Could not find </style>"

# --- 2. Remove post-open padding line and fix fit timing ---
# Find "termContainer.style.padding = '4px';" — Claude says remove it
for i, line in enumerate(lines):
    if "termContainer.style.padding = '4px';" in line:
        lines[i] = "    // REMOVED by Claude fix: padding set via CSS instead" + eol
        print(f"JS: Neutralized post-open padding at line {i+1}")
        break

# --- 3. Find the setTimeout fit block and fix it ---
for i, line in enumerate(lines):
    if "setTimeout(function() { try { if (termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus();" in line:
        lines[i] = "    setTimeout(function() { try { if (termContainer.offsetHeight > 0) { fitAddon.fit(); socket.emit('terminal_resize', { rows: term.rows, cols: term.cols }); } term.focus(); } catch(e) {} }, 100);" + eol
        print(f"JS: Fixed fit timing (100ms) + resize emit at line {i+1}")
        break

# --- 4. Fix the socket connect handler (fit BEFORE reading rows/cols) ---
connect_start = None
connect_end = None
for i, line in enumerate(lines):
    if "socket.on('connect', function() {" in line:
        connect_start = i
    if connect_start is not None and i > connect_start and "socket.emit('terminal_resize', dims)" in line:
        connect_end = i
        break

if connect_start is not None and connect_end is not None:
    new_connect = (
        "    socket.on('connect', function() {" + eol +
        "        term.writeln('\\x1b[33mACEsi Terminal connected.\\x1b[0m');" + eol +
        "        try { fitAddon.fit(); } catch(e) {}" + eol +
        "        var dims = { rows: term.rows, cols: term.cols };" + eol +
        "        socket.emit('terminal_resize', dims);" + eol +
        "    });" + eol
    )
    lines[connect_start:connect_end + 1] = [new_connect]
    print(f"JS: Rewrote socket.connect to fit-before-resize (lines {connect_start+1}-{connect_end+1})")
else:
    print("JS: WARNING - could not find socket.on('connect') block")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"PATCH COMPLETE: {len(lines)} lines")
