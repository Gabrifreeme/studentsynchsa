import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Sanity check (1-indexed 5690-5692 -> 0-indexed 5689-5691)
assert "Force xterm element to top-left" in lines[5689], f"Line 5690 mismatch: {lines[5689]!r}"
assert "querySelector('" in lines[5690], f"Line 5691 mismatch: {lines[5690]!r}"
assert "setTimeout(function()" in lines[5691], f"Line 5692 mismatch: {lines[5691]!r}"

eol = "\r\n" if lines[5690].endswith("\r\n") else "\n"

new_block = (
    "    // Force xterm element to top-left" + eol +
    "    var xtermEl = termContainer.querySelector('.xterm');" + eol +
    "    if (xtermEl) { xtermEl.style.position = 'absolute'; xtermEl.style.top = '0'; xtermEl.style.left = '0'; }" + eol +
    "    setTimeout(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} }, 250);" + eol
)

new_lines = lines[:5689] + [new_block] + lines[5692:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("SPLICE OK: Fixed line 5691 quote, replaced 5690-5692")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
