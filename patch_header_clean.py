import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the full terminal header block and replace it cleanly
pattern = re.compile(
    r'<div style="display:\s*flex;\s*justify-content:\s*space-between;[^"]*">\s*<span[^>]*>ACEsi Terminal</span>.*?</div>\s*</div>',
    re.DOTALL
)

new_header = """<div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">
        <span style="color: #ff9d00; font-weight: bold; font-family: monospace;">ACEsi Terminal</span>
        <div style="display: flex; gap: 15px;">
            <span id="terminal-min-btn" onclick="window.toggleMinimize()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">–</span>
            <span id="terminal-close-btn" onclick="window.closeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>
        </div>
    </div>"""

match = pattern.search(html)
if match:
    html = html[:match.start()] + new_header + html[match.end():]
    print("HTML: Rebuilt header with right-aligned button group")
else:
    print("WARNING: Could not find header pattern. Let me check the actual structure...")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
