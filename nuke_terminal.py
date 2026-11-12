import io, re

path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Remove ALL existing terminal JS
# Find the script block containing window.initAceTerminal
script_pattern = re.compile(r"<script>\s*window\.(openAceTerminal|initAceTerminal)\s*=.*?</script>", re.DOTALL)
html = script_pattern.sub("", html)

# 2. Remove the duplicated layout styles we injected earlier so they don't conflict
html = re.sub(r"#terminal-output\s*\{[^}]*\}", "", html)
html = re.sub(r"#terminal-panel\s*\{[^}]*\}", "", html)
html = re.sub(r"\.xterm[^{]*\{[^}]*\}", "", html)

# 3. Inject the new clean CSS
clean_css = """
#terminal-panel {
    display: none;
    flex-direction: column;
    height: 300px;
    min-height: 300px;
    background: #000;
    border-top: 1px solid #ff9d00;
    position: relative;
}
#terminal-output {
    flex: 1;
    width: 100%;
    height: 100%;
    overflow: hidden;
    padding: 0;
    margin: 0;
    background: #000;
    position: relative;
}
.xterm {
    width: 100% !important;
    height: 100% !important;
    padding: 4px;
}
.xterm-viewport::-webkit-scrollbar { width: 8px; }
.xterm-viewport::-webkit-scrollbar-track { background: #111; }
.xterm-viewport::-webkit-scrollbar-thumb { background: #ff9d00; }
"""
html = html.replace("</style>", clean_css + "\n</style>", 1)

# 4. Inject the new clean JS before </body>
new_js = """
<script>
window.openAceTerminal = function() {
    var panel = document.getElementById('terminal-panel');
    if (panel) { panel.style.display = 'flex'; }
    
    if (window.term) {
        try { window.term.dispose(); } catch(e) {}
        window.term = null;
        window.termFitAddon = null;
    }

    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            if (window.initAceTerminal) { window.initAceTerminal(); }
        });
    });
};

window.initAceTerminal = function() {
    var termContainer = document.getElementById('terminal-output');
    if (!termContainer) { return; }
    
    termContainer.innerHTML = '';
    
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
    window.termFitAddon = fitAddon; 
    window.term = term;

    term.open(termContainer);
    
    setTimeout(function() {
        try {
            fitAddon.fit();
            term.focus();
            var dims = { rows: term.rows, cols: term.cols };
            window.termSocket.emit('terminal_resize', dims);
        } catch(e) { console.error('Fit error:', e); }
    }, 500);

    var socket = io('http://127.0.0.1:5000');
    window.termSocket = socket;

    socket.on('connect', function() {
        term.writeln('\\x1b[33mACEsi Terminal connected.\\x1b[0m');
        setTimeout(function() {
            var dims = { rows: term.rows, cols: term.cols };
            socket.emit('terminal_resize', dims);
        }, 500);
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
};
</script>
"""
html = html.replace("</body>", new_js + "\n</body>")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)

print("TOTAL REBUILD COMPLETE.")
