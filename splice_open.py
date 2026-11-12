import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Sanity: verify we are cutting the right lines (1-indexed 5585-5599)
assert "window.openAceTerminal = function()" in lines[5584], f"Line 5585 mismatch: {lines[5584]!r}"
assert lines[5598].strip().startswith("};"), f"Line 5599 mismatch: {lines[5598]!r}"

eol = "\r\n" if lines[5584].endswith("\r\n") else "\n"

new_block = (
    "window.openAceTerminal = function() {" + eol +
    "    var panel = document.getElementById('terminal-panel');" + eol +
    "    if (panel) { panel.style.display = 'flex'; }" + eol +
    "    // Tear down existing xterm cleanly before rebuilding" + eol +
    "    if (window.term) {" + eol +
    "        try { window.term.dispose(); } catch(e) {}" + eol +
    "        window.term = null;" + eol +
    "        window.termFitAddon = null;" + eol +
    "    }" + eol +
    "    // Wait for layout to flush before initializing xterm" + eol +
    "    requestAnimationFrame(function() {" + eol +
    "        requestAnimationFrame(function() {" + eol +
    "            if (window.initAceTerminal) { window.initAceTerminal(); }" + eol +
    "            if (window.termFitAddon && window.term) {" + eol +
    "                try { window.termFitAddon.fit(); } catch(e) {}" + eol +
    "                try { window.term.focus(); } catch(e) {}" + eol +
    "            }" + eol +
    "        });" + eol +
    "    });" + eol +
    "};" + eol
)

new_lines = lines[:5584] + [new_block] + lines[5599:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("SPLICE OK: openAceTerminal replaced at lines 5585-5599")
print(f"Line count before: {len(lines)}, after: {len(new_lines)}")
