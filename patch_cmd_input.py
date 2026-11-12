import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the terminal panel HTML block
# Look for the closing </div> of #terminal-output, then inject the input after it
output_div_idx = None
for i, line in enumerate(lines):
    if 'id="terminal-output"' in line:
        output_div_idx = i
        break

assert output_div_idx is not None, "Could not find terminal-output div"

# Find the closing </div> after the output div
close_idx = output_div_idx
while close_idx < len(lines) and "</div>" not in lines[close_idx]:
    close_idx += 1

# Inject the clean command input AFTER that closing div
input_block = (
    '    <div style="display: flex; padding: 4px; background: #111; border-top: 1px solid #333;">' + eol +
    '        <input type="text" id="terminal-cmd-input" placeholder="Type command or Ctrl+V here, press Enter to run..." autocomplete="off" style="flex: 1; padding: 8px; background: #111; color: #ff9d00; border: 1px solid #ff9d00; outline: none; font-family: monospace; font-size: 12px;">' + eol +
    '    </div>' + eol
)

lines.insert(close_idx + 1, input_block)

# Now inject the JS that wires this input
js_block = (
    "<script>" + eol +
    "document.addEventListener('DOMContentLoaded', function() {" + eol +
    "    setTimeout(function() {" + eol +
    "        var cmdInput = document.getElementById('terminal-cmd-input');" + eol +
    "        if (!cmdInput) { console.warn('cmd-input not found'); return; }" + eol +
    "        cmdInput.addEventListener('keydown', function(e) {" + eol +
    "            if (e.key === 'Enter') {" + eol +
    "                e.preventDefault();" + eol +
    "                var cmd = cmdInput.value;" + eol +
    "                if (!cmd.trim()) return;" + eol +
    "                if (window.term && window.termSocket) {" + eol +
    "                    window.term.write(cmd + '\\r\\n');" + eol +
    "                    window.termSocket.emit('terminal_input', cmd);" + eol +
    "                }" + eol +
    "                cmdInput.value = '';" + eol +
    "            }" + eol +
    "        });" + eol +
    "        console.log('Command input wired');" + eol +
    "    }, 1500);" + eol +
    "});" + eol +
    "</script>" + eol
)

for i in range(len(lines) - 1, -1, -1):
    if "</body>" in lines[i]:
        lines.insert(i, js_block)
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"PATCH COMPLETE: command input injected at line {close_idx + 2}")
