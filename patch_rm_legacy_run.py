import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the specific block. It usually looks like:
# <div style="...">
#   <input ... placeholder="Type a command...">
#   <button ...>Run</button>
# </div>

pattern = re.compile(r'<div[^>]*>\s*<input[^>]*placeholder="Type a command\.\.\."[^>]*>\s*<button[^>]*>Run</button>\s*</div>', re.DOTALL)

if pattern.search(html):
    html = pattern.sub('', html)
    print("SUCCESS: Removed legacy command input and Run button.")
else:
    # Try a simpler pattern if the first fails
    pattern2 = re.compile(r'<input[^>]*placeholder="Type a command\.\.\."[^>]*>', re.DOTALL)
    pattern3 = re.compile(r'<button[^>]*>Run</button>', re.DOTALL)
    
    if pattern2.search(html):
        html = pattern2.sub('', html)
        print("SUCCESS: Removed legacy command input.")
    if pattern3.search(html):
        html = pattern3.sub('', html)
        print("SUCCESS: Removed legacy Run button.")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
