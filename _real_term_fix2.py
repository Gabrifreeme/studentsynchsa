p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
lines = open(p, 'r', encoding='utf-8').read().splitlines()

# Find the start of the DOMContentLoaded init (around line 5547 in 1-based, so 5546 in 0-based)
start_idx = -1
for i in range(len(lines)):
    if "document.addEventListener('DOMContentLoaded'" in lines[i] and "var termContainer" in "".join(lines[i:i+5]):
        start_idx = i
        break

if start_idx == -1:
    print("START NOT FOUND")
    exit()

# Find the end of the block (the next "});" after the socket.on('disconnect') handler)
end_idx = -1
for i in range(start_idx, len(lines)):
    if "socket.on('disconnect'" in lines[i]:
        # The block probably ends a few lines after this
        for j in range(i, min(i+10, len(lines))):
            if lines[j].strip() == "});":
                end_idx = j
                break
        if end_idx != -1:
            break

if end_idx == -1:
    print("END NOT FOUND")
    exit()

print(f"Replacing lines {start_idx+1} to {end_idx+1}")

# The clean replacement
new_block = """window.initAceTerminal = function() {
    var termContainer = document.getElementById('terminal-output');
    if (!termContainer) return;
    
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
};""".splitlines()

# Replace the block
lines[start_idx:end_idx+1] = new_block

# Now wire showTerminalPanel to call initAceTerminal
for i, line in enumerate(lines):
    if "window.showTerminalPanel = function()" in line:
        # Insert call right after panel.style.display = 'flex'
        for j in range(i, min(i+10, len(lines))):
            if "panel.style.display = 'flex'" in lines[j]:
                lines.insert(j+1, "    if (window.initAceTerminal) window.initAceTerminal();")
                break
        break

open(p, 'w', encoding='utf-8').write('\n'.join(lines))
print("TERMINAL INIT MOVED TO SHOWTERMINALPANEL")