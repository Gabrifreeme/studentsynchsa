import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "// Do not write \"connected\" immediately" in line:
        start_idx = i
    if start_idx is not None and "// Wait 1 second for shell to boot" in line:
        end_idx = i
        break

assert start_idx is not None, "Could not find start marker"
assert end_idx is not None, "Could not find end marker"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"

new_block = (
    "        // Resize after 500ms to let PowerShell boot" + eol +
    "        setTimeout(function() {" + eol +
    "            var dims = { rows: term.rows, cols: term.cols };" + eol +
    "            socket.emit('terminal_resize', dims);" + eol +
    "        }, 500);" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx + 1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Simplified resize block at lines {start_idx+1}-{end_idx+1}")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
