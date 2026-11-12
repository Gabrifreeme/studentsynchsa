import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

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
    "    var _buf = '';" + eol +
    "    term.onData(function(data) {" + eol +
    "        if (data === '\\r') {" + eol +
    "            if (_buf.length > 0) {" + eol +
    "                socket.emit('terminal_input', _buf);" + eol +
    "                _buf = '';" + eol +
    "            }" + eol +
    "        } else if (data === '\\x7f' || data === '\\x08') {" + eol +
    "            if (_buf.length > 0) {" + eol +
    "                _buf = _buf.slice(0, -1);" + eol +
    "                term.write('\\b \\b');" + eol +
    "            }" + eol +
    "        } else {" + eol +
    "            _buf += data;" + eol +
    "            term.write(data);" + eol +
    "        }" + eol +
    "    });" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx + 1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"FRONTEND: Replaced term.onData with line-buffer at lines {start_idx+1}-{end_idx+1}")
