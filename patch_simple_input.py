import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the current input HTML for the skill key
old_input = '<input id="skill-key" type="text" placeholder="e.g. skills.cooking"'

new_input = '<div style="display: flex; align-items: center; gap: 5px; margin-bottom: 10px;"><span style="color: #888; font-family: monospace;">skills.</span><input id="skill-key" type="text" placeholder="e.g. cooking"'

if old_input in html:
    html = html.replace(old_input, new_input)
    # Close the new div right after the input
    html = html.replace('style="flex:1;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:8px;font-family:monospace;outline:none;">', 'style="flex:1;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:8px;font-family:monospace;outline:none;"></div>')
    print("FRONTEND: Simplified skill input to single field with prefix")
else:
    print("WARNING: Could not find exact skill-key input line")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
