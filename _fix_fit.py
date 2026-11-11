p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Find where the terminal panel is opened
old_open = "document.getElementById('terminal-panel').style.display = 'flex';"
new_open = "document.getElementById('terminal-panel').style.display = 'flex'; if (window.termFitAddon) setTimeout(function(){ window.termFitAddon.fit(); }, 50);"

# Also save the fitAddon globally during terminal initialization
old_init = "term.loadAddon(fitAddon);"
new_init = "term.loadAddon(fitAddon); window.termFitAddon = fitAddon;"

changes = 0
if old_open in src:
    src = src.replace(old_open, new_open)
    changes += 1
if old_init in src:
    src = src.replace(old_init, new_init)
    changes += 1

if changes > 0:
    open(p, 'w', encoding='utf-8').write(src)
    print(f'FIXED {changes} LINES FOR TERMINAL RESIZING')
else:
    print('COULD NOT FIND MARKERS')
