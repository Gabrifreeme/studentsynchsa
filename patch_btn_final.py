import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Delete the Paste button entirely
import re
html = re.sub(r'<span id="terminal-paste-btn"[^>]*>Paste</span>', '', html)

# 2. Find the existing Minimize button and Close button and put them together
# First, remove whatever current minimize button exists
html = re.sub(r'<span id="terminal-min-btn"[^>]*>–</span>', '', html)

# Now inject the Minimize button right before the Close button
old_close = '<span id="terminal-close-btn"'
new_close = '<span id="terminal-min-btn" onclick="window.minimizeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;" title="Minimize">–</span><span id="terminal-close-btn"'

html = html.replace(old_close, new_close)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE: Removed Paste, moved '-' next to 'X'")
