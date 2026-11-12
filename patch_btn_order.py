import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the current header block
old_header = '<span id="terminal-min-btn" onclick="window.minimizeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;" title="Minimize (keeps server alive)">–</span><span id="terminal-paste-btn" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;">Paste</span><span id="terminal-close-btn" onclick="window.closeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>'

# Create the new header with correct order: -, Paste, X Close
new_header = '<span id="terminal-min-btn" onclick="window.minimizeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;" title="Minimize (keeps server alive)">–</span><span id="terminal-paste-btn" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;">Paste</span><span id="terminal-close-btn" onclick="window.closeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>'

if old_header in html:
    html = html.replace(old_header, new_header)
    print("HTML: Reordered header buttons (-, Paste, X Close)")
else:
    # Fallback if the string didn't match exactly, just ensure the min button exists before paste
    if 'id="terminal-min-btn"' not in html:
        html = html.replace('<span id="terminal-paste-btn"', '<span id="terminal-min-btn" onclick="window.minimizeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace; margin-right: 15px;" title="Minimize (keeps server alive)">–</span><span id="terminal-paste-btn"')
        print("HTML: Injected Minimize button before Paste")
    else:
        print("HTML: Minimize button already exists")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
