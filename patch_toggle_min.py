import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Remove old minimize/open functions
html = re.sub(r"window\.openAceTerminal = function\(\) \{.*?\n\};", "", html, flags=re.DOTALL)
html = re.sub(r"window\.minimizeAceTerminal = function\(\) \{.*?\n\};", "", html, flags=re.DOTALL)

# 2. Inject the new simple toggle logic
new_js = """
<script>
window.toggleMinimize = function() {
    var p = document.getElementById('terminal-panel');
    if (!p) return;
    
    // Check current height
    var currentHeight = parseInt(p.style.height || '300px');
    
    if (currentHeight <= 40) {
        // Expand
        p.style.setProperty('height', '300px', 'important');
        p.style.setProperty('min-height', '300px', 'important');
        p.style.setProperty('max-height', '300px', 'important');
        p.style.setProperty('display', 'flex', 'important');
    } else {
        // Shrink
        p.style.setProperty('height', '35px', 'important');
        p.style.setProperty('min-height', '35px', 'important');
        p.style.setProperty('max-height', '35px', 'important');
    }
};

window.openAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) {
        p.style.setProperty('display', 'flex', 'important');
        p.style.setProperty('height', '300px', 'important');
        p.style.setProperty('min-height', '300px', 'important');
        p.style.setProperty('max-height', '300px', 'important');
        p.removeAttribute('hidden');
    }
    if (!window.term && window.initAceTerminalFn) {
        requestAnimationFrame(function() {
            requestAnimationFrame(function() { window.initAceTerminalFn(); });
        });
    } else if (window.term) {
        setTimeout(function() { try { window.term.focus(); } catch(e) {} }, 100);
    }
};

window.closeAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) { p.style.setProperty('display', 'none', 'important'); }
};
</script>
"""
if "window.toggleMinimize" not in html:
    html = html.replace("</body>", new_js + "\n</body>")

# 3. Update the HTML button to call toggleMinimize
old_btn = 'onclick="window.minimizeAceTerminal()"'
new_btn = 'onclick="window.toggleMinimize()"'

if old_btn in html:
    html = html.replace(old_btn, new_btn)
    print("HTML: Changed button to toggleMinimize()")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
