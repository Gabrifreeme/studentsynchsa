p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Find the line where the new initAceTerminal ends (the last "};" before the next script tag or blank line)
# We'll just insert showTerminalPanel right BEFORE the initAceTerminal definition

new_show_fn = """window.showTerminalPanel = function() {
    var panel = document.getElementById('terminal-panel');
    if (!panel) return;
    panel.style.display = 'flex';
    if (window.initAceTerminal) {
        setTimeout(window.initAceTerminal, 50);
    }
};

"""

marker = "window.initAceTerminal = function() {"
if marker in src and 'window.showTerminalPanel = function()' not in src:
    src = src.replace(marker, new_show_fn + marker, 1)
    open(p, 'w', encoding='utf-8').write(src)
    print("SHOWTERMINALPANEL RESTORED")
else:
    if 'window.showTerminalPanel = function()' in src:
        print("ALREADY EXISTS")
    else:
        print("MARKER NOT FOUND")