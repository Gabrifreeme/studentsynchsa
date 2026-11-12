p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# 1. Add a global show function right after the socket connection
old_socket = "var socket = io('http://127.0.0.1:5000');"
new_socket = """var socket = io('http://127.0.0.1:5000');
    
    window.showAceTerm = function() {
        var panel = document.getElementById('terminal-panel');
        if (panel) {
            panel.style.display = 'flex';
            setTimeout(function() {
                try {
                    window.termFitAddon.fit();
                    window.acesiTerm.focus();
                } catch(e) {}
            }, 50);
        }
    };"""

if old_socket in src:
    src = src.replace(old_socket, new_socket, 1)

# 2. Replace the terminal button click to use our new function
old_btn_click = "document.getElementById('terminal-panel').style.display = 'flex';"
new_btn_click = "if (window.showAceTerm) window.showAceTerm(); else document.getElementById('terminal-panel').style.display = 'flex';"

src = src.replace(old_btn_click, new_btn_click)

open(p, 'w', encoding='utf-8').write(src)
print("TERMINAL FIT & SHOW FUNCTIONS INJECTED")