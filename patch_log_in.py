import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the terminal_output handler
old_handler = """    socket.on('terminal_output', function(data) {
        term.write(data);
    });"""

new_handler = """    socket.on('terminal_output', function(data) {
        console.log('RAW IN:', JSON.stringify(data));
        term.write(data);
    });"""

if old_handler in html:
    html = html.replace(old_handler, new_handler)
    print("FRONTEND: Added RAW IN console log")
else:
    print("FRONTEND: WARNING - Could not find terminal_output handler")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
