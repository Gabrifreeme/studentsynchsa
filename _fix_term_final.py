import re

p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# 1. Delete the OLD orphaned DOMContentLoaded that initializes the terminal too early
# It starts with: document.addEventListener('DOMContentLoaded', function() {
#     var termContainer = document.getElementById('terminal-output');
#     if (!termContainer) {
#         console.warn('Terminal container not found');
# and continues for a while

old_early_init = """document.addEventListener('DOMContentLoaded', function() {
    var termContainer = document.getElementById('terminal-output');
    if (!termContainer) {
        console.warn('Terminal container not found');
        return;
    }"""

# We need to find and remove this whole block. Let's find where it ends by counting braces.
start = src.find(old_early_init)
if start != -1:
    # Find the matching closing brace for the DOMContentLoaded block
    brace_count = 0
    in_block = False
    end = start
    for i in range(start, len(src)):
        if src[i] == '{':
            brace_count += 1
            in_block = True
        elif src[i] == '}':
            brace_count -= 1
            if in_block and brace_count == 0:
                # Find the closing ");" for the addEventListener
                end = src.find(');', i) + 2
                break
    if end > start:
        src = src[:start] + '// Old early terminal init removed - deferred to initAceTerminal()' + src[end:]
        print(f"REMOVED OLD INIT: chars {start} to {end}")
    else:
        print("COULD NOT FIND BLOCK END")
else:
    print("OLD INIT NOT FOUND (may already be gone)")

# 2. Patch showTerminalPanel to call initAceTerminal before fitting
old_show = """window.showTerminalPanel = function() {
    var panel = document.getElementById('terminal-panel');
    if (!panel) return;
    panel.style.display = 'flex';"""

new_show = """window.showTerminalPanel = function() {
    var panel = document.getElementById('terminal-panel');
    if (!panel) return;
    panel.style.display = 'flex';
    if (window.initAceTerminal && !window._aceTermReady) {
        window.initAceTerminal();
    }"""

if old_show in src:
    src = src.replace(old_show, new_show, 1)
    print("SHOWTERMINALPANEL WIRED TO INIT")

open(p, 'w', encoding='utf-8').write(src)
print("DONE")