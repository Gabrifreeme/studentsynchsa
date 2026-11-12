import io, re

path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    text = f.read()

# --- 1. Fix line 469 CSS: drop !important so flex layout can work ---
old_css = "#terminal-output { display: block !important; width: 100% !important; height: 100% !important;"
new_css = "#terminal-output { display: block; width: 100%; height: 100%;"
if old_css in text:
    text = text.replace(old_css, new_css)
    print("CSS: !important removed")
else:
    print("CSS: WARNING - line 469 pattern not matched, check manually")

# --- 2. Fix the button onclick (line 2057-2059) ---
old_btn = """onclick="
          if (window.initAceTerminal) window.initAceTerminal();
document.getElementById('terminal-panel').style.display = 'flex'
        \""""
new_btn = """onclick="window.openAceTerminal()\""""
if old_btn in text:
    text = text.replace(old_btn, new_btn)
    print("BTN: onclick replaced with openAceTerminal()")
else:
    print("BTN: WARNING - onclick pattern not matched (whitespace differs?)")

# --- 3. Fix the second call site (line 3351) ---
old_call2 = 'document.getElementById("terminal-panel").style.display = "flex"; if (window.initAceTerminal) window.initAceTerminal();'
new_call2 = 'window.openAceTerminal();'
if old_call2 in text:
    text = text.replace(old_call2, new_call2)
    print("CALL2: line 3351 replaced with openAceTerminal()")
else:
    print("CALL2: WARNING - line 3351 pattern not matched")

# --- 4. Insert openAceTerminal helper + one-shot guard into initAceTerminal ---
old_init_open = """window.initAceTerminal = function() {
    var termContainer = document.getElementById('terminal-output');
    if (!termContainer) {
        console.warn('Terminal container not found');
        return;
    }
"""
new_init_open = """window.openAceTerminal = function() {
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
};

window.initAceTerminal = function() {
    if (window.__aceTermReady) { return; }
    var termContainer = document.getElementById('terminal-output');
    if (!termContainer) {
        console.warn('Terminal container not found');
        return;
    }
    window.__aceTermReady = true;
"""
if old_init_open in text:
    text = text.replace(old_init_open, new_init_open)
    print("INIT: openAceTerminal helper added + one-shot guard installed")
else:
    print("INIT: WARNING - initAceTerminal opening pattern not matched")

# --- 5. Replace the blind 50ms setTimeout with rAF-based fit ---
old_timeout = "setTimeout(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} }, 50);"
new_timeout = "requestAnimationFrame(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} });"
if old_timeout in text:
    text = text.replace(old_timeout, new_timeout)
    print("FIT: initial fit moved to requestAnimationFrame")
else:
    print("FIT: WARNING - initial setTimeout pattern not matched")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("PATCH COMPLETE")
