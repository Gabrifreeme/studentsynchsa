import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Remove the header block we just injected
# It starts with the div containing "ACEsi Terminal" and ends with the buttons
header_pattern = re.compile(r'<div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">.*?</div>\s*</div>', re.DOTALL)
if header_pattern.search(html):
    html = header_pattern.sub('', html)
    print("HTML: Removed the header and input field")

# 2. Fix Ctrl+C handling in term.onData
# We need to find the term.onData block and add a check for \x03
old_ondata = """    term.onData(function(data) {
        if (data === '\\r') {"""
new_ondata = """    term.onData(function(data) {
        // Handle Ctrl+C explicitly
        if (data === '\\x03') {
            socket.emit('terminal_input', '\\x03');
            term.write('^C\\r\\n');
            return;
        }
        if (data === '\\r') {"""

if old_ondata in html:
    html = html.replace(old_ondata, new_ondata)
    print("JS: Added Ctrl+C handling to term.onData")
else:
    print("WARNING: Could not find exact term.onData block")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
