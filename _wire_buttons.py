p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Replace the toolbar button's inline onclick
old_inline = """document.getElementById('terminal-panel').style.display = 'flex'"""
new_inline = """if (window.showTerminalPanel) window.showTerminalPanel()"""

# Replace the other handler too
old_js = """document.getElementById("terminal-panel").style.display = "flex";"""
new_js = """if (window.showTerminalPanel) window.showTerminalPanel();"""

count = 0
if old_inline in src:
    src = src.replace(old_inline, new_inline)
    count += 1
if old_js in src:
    src = src.replace(old_js, new_js)
    count += 1

if count > 0:
    open(p, 'w', encoding='utf-8').write(src)
    print(f"WIRED {count} BUTTONS TO SHOWTERMINALPANEL")
else:
    print("NO MATCHES FOUND")