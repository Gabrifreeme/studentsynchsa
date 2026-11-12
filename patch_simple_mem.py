import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Update the placeholders in the Memory manager
html = html.replace('placeholder="Key"', 'placeholder="e.g. project.name"')
html = html.replace('placeholder="Value"', 'placeholder="What ACEsi should remember"')

# 2. Optional: Change the visual label if there is one. The current input looks like:
# <input id="mem-key" type="text" placeholder="Key" ...>
# We already changed the placeholder above.

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE: Simplified Memory manager placeholders")
