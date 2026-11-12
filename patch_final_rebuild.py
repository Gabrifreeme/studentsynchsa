import io, re

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Remove the one-shot guard that was breaking re-opens
html = html.replace("if (window.__aceTermReady) { return; }", "")
html = html.replace("window.__aceTermReady = true;", "")

# 2. Force the container to wipe its children before init
html = html.replace("termContainer.innerHTML = '';", "termContainer.innerHTML = '';\n    termContainer.style.display = 'block';\n    termContainer.style.width = '100%';\n    termContainer.style.height = '100%';")

# 3. Fix the openAceTerminal wrapper to ensure display is flex, layout is flushed, and then init runs
old_open = """window.openAceTerminal = function() {
    var panel = document.getElementById('terminal-panel');
    if (panel) { panel.style.display = 'flex'; }
    // Wait for layout to flush before initializing xterm
    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            if (window.initAceTerminal) { window.initAceTerminal(); }
            // Always re-fit after panel becomes visible
            if (window.termFitAddon && window.term) {
                try { window.termFitAddon.fit(); } catch(e) {}
                try { window.term.focus(); } catch(e) {}
            }
        });
    });
};"""

new_open = """window.openAceTerminal = function() {
    var panel = document.getElementById('terminal-panel');
    if (panel) { panel.style.display = 'flex'; }
    // Destroy old xterm instance if it exists to prevent DOM bloat
    if (window.term) {
        try { window.term.dispose(); } catch(e) {}
        window.term = null;
        window.termFitAddon = null;
    }
    // Wait for layout to flush before initializing xterm
    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            if (window.initAceTerminal) { window.initAceTerminal(); }
            // Always re-fit after panel becomes visible
            if (window.termFitAddon && window.term) {
                try { window.termFitAddon.fit(); } catch(e) {}
                try { window.term.focus(); } catch(e) {}
            }
        });
    });
};"""

if old_open in html:
    html = html.replace(old_open, new_open)
    print("FRONTEND: Forced xterm.dispose() and clean rebuild on open")
else:
    print("FRONTEND: WARNING - Could not find openAceTerminal wrapper")

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
