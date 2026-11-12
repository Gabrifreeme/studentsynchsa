p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# 1. Find the line that creates the terminal (var term = new Terminal)
# and add a global reference to it immediately after it opens.
old_open = "term.open(termContainer);"
new_open = """term.open(termContainer);
    window.acesiTerm = term;
    
    // Force focus on click
    termContainer.addEventListener('mousedown', function() {
        term.focus();
        setTimeout(function() { term.focus(); }, 10);
    });"""

if old_open in src:
    src = src.replace(old_open, new_open, 1)

# 2. When the terminal panel is opened, focus the terminal automatically
# Find where the terminal button is clicked
old_show = "document.getElementById('terminal-panel').style.display = 'flex';"
new_show = """document.getElementById('terminal-panel').style.display = 'flex';
        setTimeout(function() {
            if (window.acesiTerm) {
                window.acesiTerm.focus();
            }
        }, 200);"""

# There might be multiple places it sets display='flex', let's update all of them
src = src.replace(old_show, new_show)

open(p, 'w', encoding='utf-8').write(src)
print("TERMINAL FOCUS FIX APPLIED")