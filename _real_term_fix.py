p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Find the start and end of the broken DOMContentLoaded terminal init
start_marker = "document.addEventListener('DOMContentLoaded', function() {"
# Find the specific one that handles the terminal
start_idx = src.find("var termContainer = document.getElementById('terminal-output');", start_marker)
if start_idx == -1:
    print("MARKER 1 NOT FOUND")
    exit()

# Back up a bit to grab the DOMContentLoaded opening
start_idx = src.rfind(start_marker, 0, start_idx)

# Find the end of this DOMContentLoaded block
# It usually ends with something like "});" after the socket.on('disconnect')...
end_marker = "socket.on('disconnect', function() {"
end_idx = src.find(end_marker, start_idx)
if end_idx == -1:
    print("MARKER 2 NOT FOUND")
    exit()

# Find the closing of the disconnect block
close_idx = src.find("});", end_idx)
if close_idx == -1:
    print("CLOSING NOT FOUND")
    exit()

# We need to find the end of the DOMContentLoaded block (the next "});")
block_end = src.find("});", close_idx + 3)
if block_end == -1:
    print("BLOCK END NOT FOUND")
    exit()

block_end += 3 # Include the });

# Extract the entire init block
old_init_block = src[start_idx:block_end]

# Replace it with a clean, deferred function
new_init_block = """window.initAceTerminal = function() {
    var termContainer = document.getElementById('terminal-output');
    if (!termContainer) return;
    
    // If already initialized, just fit and focus
    if (window.termFitAddon) {
        try { window.termFitAddon.fit(); } catch(e) {}
        if (window.term) window.term.focus();
        return;
    }

    termContainer.innerHTML = '';
    termContainer.style.padding = '0';
    termContainer.style.background = '#000';
    termContainer.style.display = 'block';
    termContainer.style.width = '100%';
    termContainer.style.height = '100%';

    var term = new Terminal({
        cursorBlink: true,
        fontSize: 12,
        fontFamily: 'Consolas, monospace',
        theme: {
            background: '#000000',
            foreground: '#ff9d00',
            cursor: '#ff9d00',
            selection: '#333333'
        }
    });
    var fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    
    term.open(termContainer);
    termContainer.style.padding = '4px';
    
    // Force fit after layout settles
    setTimeout(function() {
        try { fitAddon.fit(); } catch(e) {}
        term.focus();
    }, 100);

    var socket = io('http://127.0.0.1:5000');
    
    socket.on('connect', function() {
        term.writeln('\\x1b[33mACEsi Terminal connected.\\x1b[0m');
        socket.emit('terminal_resize', { rows: term.rows, cols: term.cols });
    });
    
    socket.on('terminal_output', function(data) {
        term.write(data);
    });
    
    term.onData(function(data) {
        socket.emit('terminal_input', data);
    });
    
    window.termFitAddon = fitAddon;
    window.term = term;
    window.termSocket = socket;
};"""

# Replace the block
src = src[:start_idx] + new_init_block + src[block_end:]

# Now, find the showTerminalPanel function and call initAceTerminal() inside it
old_show = "window.showTerminalPanel = function() {\n    var panel = document.getElementById('terminal-panel');\n    if (!panel) return;\n    panel.style.display = 'flex';"
new_show = "window.showTerminalPanel = function() {\n    var panel = document.getElementById('terminal-panel');\n    if (!panel) return;\n    panel.style.display = 'flex';\n    if (window.initAceTerminal) window.initAceTerminal();"

if old_show in src:
    src = src.replace(old_show, new_show)
else:
    # Try without the spaces if the first match fails
    old_show2 = "window.showTerminalPanel = function() {"
    if old_show2 in src:
        # Inject right after the first line
        idx = src.find(old_show2) + len(old_show2)
        src = src[:idx] + "\n    if (window.initAceTerminal) window.initAceTerminal();" + src[idx:]

open(p, 'w', encoding='utf-8').write(src)
print("TERMINAL INIT MOVED TO SHOWTERMINALPANEL")