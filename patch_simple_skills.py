import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Find and replace the entire skills dialog rendering function
# The dialog is built from a giant HTML string. Let's find it.
old_dialog_start = "Skills — What Chris Knows"
idx = html.find(old_dialog_start)
assert idx != -1, "Could not find skills dialog"

# Find the opening `<div` and closing `</div>` of the dialog
# Look backward for the last "var html =" or "html +="
# Look for the pattern: html += '<div...' before our marker
# Search backward for "html"
search_start = html.rfind("html =", 0, idx)
assert search_start != -1, "Could not find html variable"
search_start2 = html.rfind("html +=", 0, idx)
if search_start2 != -1 and search_start2 > search_start:
    search_start = search_start2

# Find the end - look for `</div>' +` after the marker
end_marker = "'</div>' +"
search_end = html.find(end_marker, idx)
assert search_end != -1, "Could not find dialog end"
search_end += len(end_marker)

# Get the block we're replacing
old_block = html[search_start:search_end]
print(f"Found block: {len(old_block)} chars")

# Build the new simpler dialog
new_block = """html = `
<div id="skills-dialog" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #111; border: 1px solid #ff9d00; padding: 20px; z-index: 10000; width: 600px; max-height: 80vh; overflow-y: auto; font-family: monospace; color: #ff9d00; box-shadow: 0 4px 20px rgba(0,0,0,0.8);">
    <div style="font-weight: bold; font-size: 14px; margin-bottom: 15px;">Skills — What Chris Knows</div>
    <div id="skills-list-container"></div>

    <hr style="border: 0; border-top: 1px solid #333; margin: 15px 0;">

    <div style="font-weight: bold; font-size: 13px; margin-bottom: 10px;">Add New Skill</div>
    <div style="display: flex; gap: 8px; margin-bottom: 10px;">
        <span style="color: #888; padding: 8px 0;">skills.</span>
        <input id="skill-key" type="text" placeholder="cooking (no prefix)" style="flex: 1; background: #000; color: #ff9d00; border: 1px solid #ff9d00; padding: 8px; font-family: monospace; font-size: 12px; outline: none;">
    </div>
    <textarea id="skill-val" placeholder="What can ACEsi do? e.g. 'Cook pasta. Boil water. Add pasta...'" style="width: 100%; height: 80px; background: #000; color: #ff9d00; border: 1px solid #ff9d00; padding: 8px; font-family: monospace; font-size: 12px; outline: none; margin-bottom: 10px;"></textarea>
    <button onclick="setSkill()" style="background: #ff9d00; color: #000; border: none; padding: 8px 20px; font-family: monospace; font-weight: bold; cursor: pointer;">Add</button>
    <button onclick="closeSkillsManager()" style="background: #333; color: #ff9d00; border: 1px solid #ff9d00; padding: 8px 20px; font-family: monospace; font-weight: bold; cursor: pointer; margin-left: 8px;">Close</button>
</div>
` + '</div>';"""

html = html[:search_start] + new_block + html[search_end:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE: Simplified skills dialog")
