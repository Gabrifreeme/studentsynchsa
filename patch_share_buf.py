import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find term.onData block
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
    "    window._aceBuf = '';" + eol +
    "    term.onData(function(data) {" + eol +
    "        if (data === '\\r') {" + eol +
    "            if (window._aceBuf.length > 0) {" + eol +
    "                socket.emit('terminal_input', window._aceBuf);" + eol +
    "                window._aceBuf = '';" + eol +
    "            }" + eol +
    "        } else if (data === '\\x7f' || data === '\\x08') {" + eol +
    "            if (window._aceBuf.length > 0) {" + eol +
    "                window._aceBuf = window._aceBuf.slice(0, -1);" + eol +
    "                term.write('\\b \\b');" + eol +
    "            }" + eol +
    "        } else {" + eol +
    "            window._aceBuf += data;" + eol +
    "            term.write(data);" + eol +
    "        }" + eol +
    "    });" + eol
)

lines[start_idx:end_idx+1] = [new_block]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: term.onData uses window._aceBuf at lines {start_idx+1}-{end_idx+1}")
