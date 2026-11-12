import io, re
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
py_path = r"C:\Users\chris\LipSyncStudent\server.py"

# --- FRONTEND FIX ---
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find term.onData and inject local backspace handling
old_ondata = """    term.onData(function(data) {
        socket.emit('terminal_input', data);
    });"""

new_ondata = """    term.onData(function(data) {
        // Handle Backspace locally so the screen updates instantly
        if (data === '\\x7f' || data === '\\x08') {
            term.write('\\b \\b');
        }
        socket.emit('terminal_input', data);
    });"""

if old_ondata in html:
    html = html.replace(old_ondata, new_ondata)
    print("FRONTEND: Injected local backspace handler")
else:
    print("FRONTEND: WARNING - Could not find exact term.onData block")

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)

# --- BACKEND FIX ---
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the terminal_input handler and replace it with a raw byte pass-through
start_idx = None
for i, line in enumerate(lines):
    if "@socketio.on('terminal_input')" in line:
        start_idx = i
        break

assert start_idx is not None, "Could not find terminal_input handler"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"

# Replace the whole handler (approx 15 lines) with a 5-line pass-through
new_block = (
    "@socketio.on('terminal_input')" + eol +
    "def handle_terminal_input(data):" + eol +
    "    global terminal_process" + eol +
    "    if terminal_process and terminal_process.isalive():" + eol +
    "        try:" + eol +
    "            terminal_process.write(data)" + eol +
    "        except Exception:" + eol +
    "            pass" + eol
)

# Find the end of the current handler (the next @socketio.on line)
end_idx = start_idx + 1
while end_idx < len(lines) and not lines[end_idx].startswith("@socketio"):
    end_idx += 1

lines[start_idx:end_idx] = [new_block]

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("BACKEND: Restored raw byte pass-through")
print("PATCH COMPLETE")
