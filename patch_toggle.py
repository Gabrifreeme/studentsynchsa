import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Remove the brute-force close listener
html = re.sub(r"<script>\s*// BRUTEFORCE CLOSE BUTTON FIX.*?</script>", "", html, flags=re.DOTALL)

# 2. Fix the Close button (remove inline onclick, add clean onclick)
html = re.sub(
    r'<span id="terminal-close-btn"[^>]*>X Close</span>',
    '<span id="terminal-close-btn" onclick="window.closeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>',
    html
)

# 3. Fix the Terminal button to call toggleAceTerminal
html = html.replace(
    'onclick="window.openAceTerminal()"',
    'onclick="window.toggleAceTerminal()"'
)

# 4. Inject the toggle/close functions at the end of the body
js = """
<script>
window.toggleAceTerminal = function() {
    var panel = document.getElementById('terminal-panel');
    if (!panel) return;
    if (panel.style.display === 'flex') {
        panel.style.display = 'none';
    } else {
        window.openAceTerminal();
    }
};

window.closeAceTerminal = function() {
    var panel = document.getElementById('terminal-panel');
    if (panel) panel.style.display = 'none';
};
</script>
"""
if "window.toggleAceTerminal" not in html:
    html = html.replace("</body>", js + "\n</body>")
    print("JS: Injected toggle/close functions")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)

print("PATCH COMPLETE")
