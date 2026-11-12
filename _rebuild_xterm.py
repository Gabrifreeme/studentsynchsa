p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Find the terminal init block: starts at "var term = new Terminal({" and ends at "term.open(termContainer);"
import re

old_open = "term.open(termContainer);"
new_open = """// Rebuild terminal if container has no dimensions yet
    function initXterm() {
        if (!termContainer || termContainer.clientWidth === 0) {
            // Panel not visible yet, skip - will retry when shown
            window._termPending = true;
            return false;
        }
        term.open(termContainer);
        setTimeout(function() {
            try { fitAddon.fit(); } catch(e) {}
        }, 50);
        return true;
    }
    if (!initXterm()) {
        // defer until panel is shown
        window._deferredTermInit = initXterm;
    }"""

# Replace the single term.open() call
if old_open in src and 'function initXterm' not in src:
    src = src.replace(old_open, new_open, 1)
    open(p, 'w', encoding='utf-8').write(src)
    print("XTERM DEFERRED INIT")
else:
    print("ALREADY PATCHED OR MARKER MISSING")