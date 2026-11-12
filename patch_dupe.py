import io, re

path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Find EVERY <div id="terminal-panel"> block and remove them all
# We match from <div id="terminal-panel" until the matching </div> for the panel
# Since there might be nested divs, we use a very aggressive match:
html = re.sub(r'<div id="terminal-panel".*?<div id="terminal-output".*?<\/div>\s*<\/div>', '', html, flags=re.DOTALL)

# 2. Find and remove any leftover orphan terminal-output divs
html = re.sub(r'<div id="terminal-output".*?<\/div>', '', html, flags=re.DOTALL)

# 3. Find and remove any leftover stray terminal-panel divs
html = re.sub(r'<div id="terminal-panel".*?<\/div>', '', html, flags=re.DOTALL)

# 4. Now inject ONE clean terminal panel right before </body>
clean_panel = """
<div id="terminal-panel" style="display: none; flex-direction: column; height: 300px; min-height: 300px; max-height: 300px; position: relative; background: #000; border-top: 1px solid #ff9d00;">
    <div style="display: flex; justify-content: space-between; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">
        <span style="color: #ff9d00; font-family: monospace; font-weight: bold; font-size: 12px;">ACEsi Terminal</span>
        <span onclick="document.getElementById('terminal-panel').style.display='none'" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>
    </div>
    <div id="terminal-output" style="flex: 1; height: 270px; width: 100%; overflow: hidden; padding: 0; margin: 0; background: #000; position: relative;"></div>
</div>
"""
html = html.replace("</body>", clean_panel + "\n</body>")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Deleted all duplicate terminal panels, injected one clean panel.")
