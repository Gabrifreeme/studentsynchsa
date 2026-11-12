import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11189].endswith("\r\n") else "\n"

# Verify (1-indexed 11190 and 11208 -> 0-indexed 11189 and 11207)
assert "window.openAceTerminal = function()" in lines[11189], f"L11190 mismatch: {lines[11189]!r}"
assert lines[11207].strip() == "};", f"L11208 mismatch: {lines[11207]!r}"

new_block = (
    "window.openAceTerminal = function() {" + eol +
    "    var panel = document.getElementById('terminal-panel');" + eol +
    "    if (panel) {" + eol +
    "        panel.style.display = 'flex';" + eol +
    "        panel.style.setProperty('height', '300px', 'important');" + eol +
    "        panel.style.setProperty('min-height', '300px', 'important');" + eol +
    "        panel.style.setProperty('max-height', '300px', 'important');" + eol +
    "    }" + eol +
    "    // Do NOT dispose the terminal. Keep history and server connection alive." + eol +
    "    if (!window.term) {" + eol +
    "        requestAnimationFrame(function() {" + eol +
    "            requestAnimationFrame(function() {" + eol +
    "                window.initAceTerminalFn();" + eol +
    "            });" + eol +
    "        });" + eol +
    "    } else {" + eol +
    "        // Terminal already exists - just focus it" + eol +
    "        setTimeout(function() { try { window.term.focus(); } catch(e) {} }, 100);" + eol +
    "    }" + eol +
    "};" + eol
)

new_lines = lines[:11189] + [new_block] + lines[11208:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: openAceTerminal rewritten, no more dispose")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
