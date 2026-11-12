import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find "term.open(termContainer);" as anchor
open_idx = None
for i, line in enumerate(lines):
    if "term.open(termContainer);" in line:
        open_idx = i
        break

assert open_idx is not None, "Could not find term.open(termContainer);"

# Inject paste handler right after term.open
paste_block = (
    "    // Handle Ctrl+V / Shift+Insert paste" + eol +
    "    termContainer.addEventListener('paste', function(e) {" + eol +
    "        e.preventDefault();" + eol +
    "        var text = (e.clipboardData || window.clipboardData).getData('text');" + eol +
    "        if (text) {" + eol +
    "            _buf += text;" + eol +
    "            term.write(text);" + eol +
    "        }" + eol +
    "    });" + eol
)

# Insert AFTER the term.open line
lines.insert(open_idx + 1, paste_block)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: Paste listener after term.open at line {open_idx+1}")
