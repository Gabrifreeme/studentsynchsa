import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find where initAceTerminal sets window.term = term;
term_assign_idx = None
for i, line in enumerate(lines):
    if "window.term = term;" in line:
        term_assign_idx = i
        break

assert term_assign_idx is not None, "Could not find 'window.term = term;'"

eol = "\r\n" if lines[term_assign_idx].endswith("\r\n") else "\n"

# Inject the JS right after window.term = term;
inject_js = (
    "    setTimeout(function() {" + eol +
    "        var screen = termContainer.querySelector('.xterm-screen');" + eol +
    "        var viewport = termContainer.querySelector('.xterm-viewport');" + eol +
    "        var rows = termContainer.querySelector('.xterm-rows');" + eol +
    "        if (screen) { screen.style.position = 'absolute'; screen.style.top = '0'; screen.style.left = '0'; screen.style.textAlign = 'left'; }" + eol +
    "        if (rows) { rows.style.textAlign = 'left'; }" + eol +
    "        if (viewport) { viewport.style.overflowY = 'scroll'; }" + eol +
    "        if (window.term) {" + eol +
    "            term.refresh(0, term.rows - 1);" + eol +
    "        }" + eol +
    "    }, 300);" + eol
)

lines.insert(term_assign_idx + 1, inject_js)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: Force absolute lock after window.term at line {term_assign_idx+1}")
