p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Look for the terminal button / where the panel becomes visible
# and inject a call to window.initAceTerminal()

# The display='flex' line is where the panel opens
old_open = "document.getElementById('terminal-panel').style.display = 'flex';"
new_open = "document.getElementById('terminal-panel').style.display = 'flex'; if (window.initAceTerminal) setTimeout(window.initAceTerminal, 50);"

count = src.count(old_open)
if count > 0:
    src = src.replace(old_open, new_open)
    open(p, 'w', encoding='utf-8').write(src)
    print(f"WIRED TERMINAL INIT TO {count} BUTTON(S)")
else:
    print("TERMINAL BUTTON CLICK HANDLER NOT FOUND")