import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find where the terminal is opened
for i, line in enumerate(lines):
    if "term.open(termContainer);" in line:
        open_idx = i
        break

assert open_idx is not None, "Could not find term.open(termContainer);"

# Inject the fix right after term.open
inject = (
    "    term.open(termContainer);" + eol +
    "    // Allow right-click for paste" + eol +
    "    termContainer.addEventListener('contextmenu', function(e) { e.stopPropagation(); });" + eol +
    "    // Auto-scroll to bottom on new output" + eol +
    "    var originalWrite = term.write.bind(term);" + eol +
    "    term.write = function(data) {" + eol +
    "        originalWrite(data);" + eol +
    "        term.scrollToBottom();" + eol +
    "    };" + eol
)

lines[open_idx] = inject

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: Right-click + auto-scroll at line {open_idx+1}")
