import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

old_placeholder = 'placeholder="What Chris knows/can do"'
new_placeholder = 'placeholder="What ACEsi can do"'

if old_placeholder in html:
    html = html.replace(old_placeholder, new_placeholder)
    print("FRONTEND: Changed placeholder to 'What ACEsi can do'")
else:
    print("WARNING: Could not find the exact placeholder text")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
