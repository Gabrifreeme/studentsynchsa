import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Replace the existing toggle/close functions with a bulletproof version
import re
html = re.sub(r"<script>\s*window\.toggleAceTerminal = function\(\).*?</script>", "", html, flags=re.DOTALL)
html = re.sub(r"<script>\s*// BRUTEFORCE CLOSE BUTTON FIX.*?</script>", "", html, flags=re.DOTALL)

new_js = """
<script>
window.closeAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) {
        p.style.setProperty('display', 'none', 'important');
        p.setAttribute('hidden', 'true');
    }
};
window.openAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) {
        p.removeAttribute('hidden');
        p.style.removeProperty('display');
        p.style.display = 'flex';
    }
    if (window.initAceTerminal) {
        requestAnimationFrame(function() {
            requestAnimationFrame(window.initAceTerminal);
        });
    }
};
window.toggleAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (!p) return;
    if (p.hasAttribute('hidden') || p.style.display === 'none') {
        window.openAceTerminal();
    } else {
        window.closeAceTerminal();
    }
};
</script>
"""
if "window.closeAceTerminal = function()" not in html or "p.style.setProperty('display', 'none', 'important')" not in html:
    html = html.replace("</body>", new_js + "\n</body>")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE: Frontend toggle/close fixed")
