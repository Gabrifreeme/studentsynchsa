import re

p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Find the entire xterm init block, from "var term = new Terminal" 
# all the way to "socket.on('disconnect', function() { ..."
# and replace it with a clean, deferred initialization.

start_marker = "var term = new Terminal({"
end_marker = "socket.on('disconnect', function() {"

start_idx = src.find(start_marker)
if start_idx == -1:
    print("START MARKER NOT FOUND")
    exit()

end_idx = src.find(end_marker, start_idx)
if end_idx == -1:
    print("END MARKER NOT FOUND")
    exit()

# We'll keep everything up to "socket.on('disconnect'"
new_block = """window.initAceTerminal = function() {
    var termContainer = document.getElementById('terminal-output');
    if (!termContainer) return;
    
    // If already initialized, skip
    if (window._aceTermReady) {
        if (window.termFitAddon) { try { window.termFitAddon.fit(); } catch(e) {} }
        if (window.acesiTerm) window.acesiTerm.focus();
        return;
    }
    
    termContainer.innerHTML = '';
    termContainer.style.background = '#000';
    termContainer.style.padding = '0';
    termContainer.style.margin = '0';
    termContainer.style.display = 'block';
    termContainer.style.width = '100%';
    termContainer.style.height = '100%';
    termContainer.style.position = 'relative';
    
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
    
    // Force a fit AFTER layout is settled
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
    
    window.addEventListener('resize', function() {
        try {
            fitAddon.fit();
            socket.emit('terminal_resize', { rows: term.rows, cols: term.cols });
        } catch(e) {}
    });
    
    window.acesiTerm = term;
    window.termFitAddon = fitAddon;
    window.termSocket = socket;
    window._aceTermReady = true;
};

// Auto-init when panel opens
document.addEventListener('DOMContentLoaded', function() {
    var panel = document.getElementById('terminal-panel');
    if (panel && panel.style.display !== 'none') {
        setTimeout(window.initAceTerminal, 200);
    }
});
"""

src = src[:start_idx] + new_block + src[end_idx:]

open(p, 'w', encoding='utf-8').write(src)
print("XTERM COMPLETELY REBUILT - DEFERRED INIT")