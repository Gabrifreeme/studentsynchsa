import io, re

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. REMOVE the broken HTML block (from <div id="terminal-panel"> to its closing </div>)
# We look for the exact opening tag and find the next closing div
# Since we don't know the exact state, we'll use a regex to strip it
html = re.sub(r'<div id="terminal-panel".*?<\/div>\s*<\/div>\s*<\/div>', '', html, flags=re.DOTALL)
html = re.sub(r'<div id="terminal-panel".*?<\/div>', '', html, flags=re.DOTALL)

# 2. Inject the clean HTML right before the closing </body> or near where it was
# Let's put it at the end of the body so it's guaranteed to be in the DOM
clean_html = """
<div id="terminal-panel" style="display: none; flex-direction: column; height: 300px; min-height: 300px; max-height: 300px; position: relative; background: #000; border-top: 1px solid #ff9d00;">
    <div style="display: flex; justify-content: space-between; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">
        <span style="color: #ff9d00; font-family: monospace; font-weight: bold; font-size: 12px;">ACEsi Terminal</span>
        <span onclick="document.getElementById('terminal-panel').style.display='none'" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>
    </div>
    <div id="terminal-output" style="flex: 1; height: 270px; width: 100%; overflow: hidden; padding: 0; margin: 0; background: #000; position: relative;"></div>
</div>
"""
html = html.replace("</body>", clean_html + "\n</body>")

# 3. REMOVE all broken JS terminal blocks
html = re.sub(r"<script>\s*window\.(openAceTerminal|initAceTerminal)\s*=.*?</script>", "", html, flags=re.DOTALL)

# 4. Inject the fresh JS
clean_js = """
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
    if (!termContainer) { console.warn('No term container'); return; }
    
    termContainer.innerHTML = '';
    
    var term = new Terminal({
        cursorBlink: true,
        rows: 24,
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
        try { fitAddon.fit(); term.focus(); } catch(e) {}
        var socket = io('http://127.0.0.1:5000');
        window.termSocket = socket;
        
        socket.on('connect', function() {
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
    }, 500);
};
</script>
"""
html = html.replace("</body>", clean_js + "\n</body>")

# 5. Inject the clean CSS
css = """
#terminal-panel {
    display: none;
    flex-direction: column;
    height: 300px;
    min-height: 300px;
    max-height: 300px;
    background: #000;
    border-top: 1px solid #ff9d00;
    position: relative;
}
#terminal-output {
    flex: 1;
    height: 270px;
    width: 100%;
    overflow: hidden;
    padding: 0;
    margin: 0;
    background: #000;
    position: relative;
}
.xterm { height: 270px !important; width: 100% !important; padding: 4px !important; }
.xterm .xterm-viewport { overflow-y: scroll !important; overflow-x: hidden !important; height: 270px !important; }
.xterm-viewport::-webkit-scrollbar { width: 10px !important; }
.xterm-viewport::-webkit-scrollbar-track { background: #111 !important; }
.xterm-viewport::-webkit-scrollbar-thumb { background: #ff9d00 !important; border-radius: 5px !important; }
"""
html = html.replace("</style>", css + "\n</style>", 1)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Clean slate HTML, JS, and CSS injected. No more regex butchers.")
