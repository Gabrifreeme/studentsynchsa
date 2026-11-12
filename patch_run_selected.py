import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find "checks.forEach(function (c, index)" and the closing "});"
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "checks.forEach(function (c, index)" in line:
        start_idx = i
    if start_idx is not None and i > start_idx and line.strip() == "});":
        end_idx = i
        break

assert start_idx is not None, "Could not find checks.forEach"
assert end_idx is not None, "Could not find closing });"

new_block = (
    "        checks.forEach(function (c, index) {" + eol +
    "          setTimeout(function() {" + eol +
    "            var cmd = c.value;" + eol +
    "            var isLong = /^\\s*(flutter\\s+run|dart\\s+run|python\\s+server|npm\\s+start)/i.test(cmd);" + eol +
    "            if (isLong) {" + eol +
    "              fetch('http://127.0.0.1:5000/run', {" + eol +
    "                method: 'POST'," + eol +
    "                headers: {'Content-Type': 'application/json'}," + eol +
    "                body: JSON.stringify({command: cmd})" + eol +
    "              }).then(function(r) { return r.json(); }).then(function(d) {" + eol +
    "                if (window.term) { window.term.write('\\r\\n\\x1b[33m[RUN] ' + (d.output || '') + '\\x1b[0m\\r\\n'); }" + eol +
    "              }).catch(function(e) {" + eol +
    "                if (window.term) { window.term.write('\\r\\n\\x1b[31m[ERROR] ' + e.message + '\\x1b[0m\\r\\n'); }" + eol +
    "              });" + eol +
    "            } else {" + eol +
    "              if (window.term && window.termSocket) {" + eol +
    "                window.term.write(cmd + '\\r\\n');" + eol +
    "                window.termSocket.emit('terminal_input', cmd);" + eol +
    "              }" + eol +
    "            }" + eol +
    "          }, index * 1500);" + eol +
    "        });" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx+1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("SPLICE OK: runSelected() rewritten")
