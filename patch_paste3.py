import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

buf_idx = None
for i, line in enumerate(lines):
    if "var _buf = '';" in line:
        buf_idx = i
        break

assert buf_idx is not None, "Could not find 'var _buf' declaration"

paste_block = (
    "    termContainer.addEventListener('paste', function(e) {" + eol +
    "        e.preventDefault();" + eol +
    "        var text = (e.clipboardData || window.clipboardData).getData('text');" + eol +
    "        if (text) {" + eol +
    "            _buf += text;" + eol +
    "            term.write(text);" + eol +
    "        }" + eol +
    "    });" + eol
)

lines.insert(buf_idx + 1, paste_block)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: Paste listener after _buf declaration at line {buf_idx+1}")
