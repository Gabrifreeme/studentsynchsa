import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Find the whole terminal header block and rebuild it cleanly
old_header_pattern = re.compile(
    r'<div style="display: flex; justify-content: space-between; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">.*?<span id="terminal-close-btn".*?</span>\s*</div>',
    re.DOTALL
)

new_header = """<div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">
        <span style="color: #ff9d00; font-weight: bold; font-family: monospace;">ACEsi Terminal</span>
        <div>
            <span id="terminal-min-btn" onclick="window.minimizeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;" title="Minimize">-</span>
            <span id="terminal-close-btn" onclick="window.closeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>
        </div>
    </div>"""

if old_header_pattern.search(html):
    html = old_header_pattern.sub(new_header, html)
    print("HTML: Rebuilt header with grouped buttons")
else:
    print("HTML: WARNING - Could not find exact header pattern")

# 2. Fix the minimize JS to force the height
minimize_js = """
<script>
window.minimizeAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) {
        p.style.setProperty('height', '35px', 'important');
        p.style.setProperty('min-height', '35px', 'important');
        p.style.setProperty('max-height', '35px', 'important');
    }
};
</script>
"""

# Remove old minimize logic if it exists
html = re.sub(r"<script>\s*window\.minimizeAceTerminal = function\(\).*?</script>", "", html, flags=re.DOTALL)
html = html.replace("</body>", minimize_js + "\n</body>")
print("JS: Injected clean minimize logic")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
