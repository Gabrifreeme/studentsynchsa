import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Add a Paste button next to the Close button
old_header = '<span id="terminal-close-btn" onclick="window.closeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>'
new_header = (
    '<span id="terminal-paste-btn" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;">Paste</span>' +
    old_header
)

if "terminal-paste-btn" not in html:
    html = html.replace(old_header, new_header)
    print("HTML: Added Paste button to terminal header")
else:
    print("HTML: Paste button already exists")

# 2. Wire the Paste button
# Find where term is initialized and _buf is declared
paste_js = """
    var pasteBtn = document.getElementById('terminal-paste-btn');
    if (pasteBtn) {
        pasteBtn.addEventListener('click', function() {
            navigator.clipboard.readText().then(function(text) {
                if (text) {
                    if (typeof _buf !== 'undefined') {
                        _buf += text;
                    }
                    term.write(text);
                }
            }).catch(function(err) {
                console.error('Paste failed:', err);
            });
        });
    }
"""

# Inject it right after the _buf declaration
old_buf = "    var _buf = '';"
new_buf = old_buf + "\n" + paste_js

if "_buf" in html and "terminal-paste-btn" not in html.split(old_buf)[1] if old_buf in html else True:
    # Only inject if the paste_js block isn't already there
    if "navigator.clipboard.readText()" not in html:
        html = html.replace(old_buf, new_buf)
        print("JS: Injected clipboard paste logic")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
