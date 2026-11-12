import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Force the terminal panel to start hidden in the HTML
html = re.sub(r'<div id="terminal-panel" style="[^"]*"', '<div id="terminal-panel" style="display: none; flex-direction: column; height: 300px; min-height: 300px; max-height: 300px; background: #000; border-top: 1px solid #ff9d00; position: relative;"', html)

# 2. Fix the Terminal button to call toggle
html = html.replace('onclick="window.openAceTerminal()"', 'onclick="window.toggleAceTerminal()"')
html = html.replace('onclick="window.toggleAceTerminal()"', 'onclick="window.toggleAceTerminal()"') # ensure single

# 3. Fix the Close button to call close
html = html.replace('onclick="document.getElementById(\'terminal-panel\').style.display=\'none\'"', 'onclick="window.closeAceTerminal()"')

# 4. Inject the toggle/close functions right before </body> if they aren't already there properly
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
if "window.toggleAceTerminal = function() {" not in html:
    html = html.replace("</body>", js + "\n</body>")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("PATCH COMPLETE: HTML forced to hidden, buttons wired to toggle/close")
