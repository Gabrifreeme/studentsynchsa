import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Verify we're cutting the right block
assert "<script>" in lines[5573], f"L5574 mismatch: {lines[5573]!r}"
assert "document.addEventListener('DOMContentLoaded'" in lines[5574], f"L5575 mismatch: {lines[5574]!r}"
assert "term.write(data)" in lines[5619], f"L5620 mismatch: {lines[5619]!r}"

eol = "\r\n" if lines[5574].endswith("\r\n") else "\n"

new_block = (
    "<script>" + eol +
    "window.openAceTerminal = function() {" + eol +
    "    var panel = document.getElementById('terminal-panel');" + eol +
    "    if (panel) { panel.style.display = 'flex'; }" + eol +
    "    if (window.term) { try { window.term.dispose(); } catch(e) {} window.term = null; }" + eol +
    "    requestAnimationFrame(function() {" + eol +
    "        requestAnimationFrame(function() { window.initAceTerminal(); });" + eol +
    "    });" + eol +
    "};" + eol +
    "" + eol +
    "window.initAceTerminal = function() {" + eol +
    "    var termContainer = document.getElementById('terminal-output');" + eol +
    "    if (!termContainer) { return; }" + eol +
    "    termContainer.innerHTML = '';" + eol +
    "    termContainer.style.background = '#000';" + eol +
    "    termContainer.style.padding = '4px';" + eol +
    "    termContainer.style.display = 'block';" + eol +
    "    termContainer.style.width = '100%';" + eol +
    "    termContainer.style.height = '100%';" + eol +
    "    var term = new Terminal({" + eol +
    "        rows: 24," + eol +
    "        cols: 80," + eol +
    "        cursorBlink: true," + eol +
    "        scrollback: 1000," + eol +
    "        fontSize: 12," + eol +
    "        fontFamily: 'Consolas, monospace'," + eol +
    "        theme: {" + eol +
    "            background: '#000000'," + eol +
    "            foreground: '#ff9d00'," + eol +
    "            cursor: '#ff9d00'," + eol +
    "            selection: '#333333'" + eol +
    "        }" + eol +
    "    });" + eol +
    "    window.term = term;" + eol +
    "    term.open(termContainer);" + eol +
    "    setTimeout(function() { try { term.focus(); } catch(e) {} }, 500);" + eol +
    "    var socket = io('http://127.0.0.1:5000');" + eol +
    "    window.termSocket = socket;" + eol +
    "    socket.on('connect', function() {" + eol +
    "        var dims = { rows: term.rows, cols: term.cols };" + eol +
    "        socket.emit('terminal_resize', dims);" + eol +
    "    });" + eol +
    "    socket.on('terminal_output', function(data) {" + eol +
    "        term.write(data);" + eol +
    "    });" + eol
)

new_lines = lines[:5573] + [new_block] + lines[5620:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: openAceTerminal + initAceTerminal injected")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
