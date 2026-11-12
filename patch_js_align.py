import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the exact line: term.open(termContainer);
for i, line in enumerate(lines):
    if "term.open(termContainer);" in line:
        open_idx = i
        break

assert open_idx is not None, "Could not find term.open(termContainer);"

# Inject the JS lock immediately after term.open
inject_js = (
    "    term.open(termContainer);" + eol +
    "    setTimeout(function() {" + eol +
    "        var xterm = termContainer.querySelector('.xterm');" + eol +
    "        var screen = termContainer.querySelector('.xterm-screen');" + eol +
    "        var rows = termContainer.querySelector('.xterm-rows');" + eol +
    "        if (xterm) { xterm.style.position = 'absolute'; xterm.style.top = '0'; xterm.style.left = '0'; xterm.style.padding = '0'; xterm.style.margin = '0'; }" + eol +
    "        if (screen) { screen.style.position = 'absolute'; screen.style.top = '0'; screen.style.left = '0'; screen.style.textAlign = 'left'; }" + eol +
    "        if (rows) { rows.style.textAlign = 'left'; }" + eol +
    "        term.refresh(0, term.rows - 1);" + eol +
    "    }, 150);" + eol
)

lines[open_idx] = inject_js

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: JS alignment lock after term.open at line {open_idx+1}")
