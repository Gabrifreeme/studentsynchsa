import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Update openAceTerminal to restore height
old_open = """window.openAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) {
        p.removeAttribute('hidden');
        p.style.removeProperty('display');
        p.style.display = 'flex';
    }
    // Only initialize if it doesn't already exist
    if (!window.term && window.initAceTerminal) {
        requestAnimationFrame(function() {
            requestAnimationFrame(window.initAceTerminal);
        });
    } else if (window.term) {
        // Re-focus the existing terminal
        setTimeout(function() { try { window.term.focus(); } catch(e) {} }, 100);
    }
};"""

new_open = """window.openAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) {
        p.removeAttribute('hidden');
        p.style.removeProperty('display');
        p.style.display = 'flex';
        // Restore full height when reopening
        p.style.setProperty('height', '300px', 'important');
        p.style.setProperty('min-height', '300px', 'important');
        p.style.setProperty('max-height', '300px', 'important');
    }
    // Only initialize if it doesn't already exist
    if (!window.term && window.initAceTerminal) {
        requestAnimationFrame(function() {
            requestAnimationFrame(window.initAceTerminal);
        });
    } else if (window.term) {
        setTimeout(function() { try { window.term.focus(); } catch(e) {} }, 100);
    }
};"""

if old_open in html:
    html = html.replace(old_open, new_open)
    print("FRONTEND: Fixed openAceTerminal to restore height")
else:
    print("FRONTEND: WARNING - Could not find openAceTerminal block")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
