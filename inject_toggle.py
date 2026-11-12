import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the LAST </body> in the file
last_body = None
for i in range(len(lines) - 1, -1, -1):
    if "</body>" in lines[i]:
        last_body = i
        break

assert last_body is not None, "Could not find </body>"

# Inject the functions right before </body>
js_block = (
    "<script>" + eol +
    "window.toggleAceTerminal = function() {" + eol +
    "    var panel = document.getElementById('terminal-panel');" + eol +
    "    if (!panel) return;" + eol +
    "    if (panel.style.display === 'flex') {" + eol +
    "        panel.style.display = 'none';" + eol +
    "    } else {" + eol +
    "        window.openAceTerminal();" + eol +
    "    }" + eol +
    "};" + eol +
    "window.closeAceTerminal = function() {" + eol +
    "    var panel = document.getElementById('terminal-panel');" + eol +
    "    if (panel) panel.style.display = 'none';" + eol +
    "};" + eol +
    "</script>" + eol
)

lines.insert(last_body, js_block)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: toggle/close functions before </body> at line {last_body+1}")
