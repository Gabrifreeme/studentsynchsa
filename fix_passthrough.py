import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find term.onData and replace it with a pure pass-through
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "term.onData(function(data)" in line:
        start_idx = i
    if start_idx is not None and i > start_idx and line.strip() == "});":
        end_idx = i
        break

assert start_idx is not None, "Could not find term.onData"
assert end_idx is not None, "Could not find closing }); for term.onData"

new_block = (
    "    term.onData(function(data) {" + eol +
    "        socket.emit('terminal_input', data);" + eol +
    "    });" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx + 1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: term.onData reset to pure pass-through at lines {start_idx+1}-{end_idx+1}")
