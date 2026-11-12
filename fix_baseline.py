import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[5590].endswith("\r\n") else "\n"

# --- VERIFY (0-indexed) ---
assert "var term = new Terminal({" in lines[5589], f"L5590 mismatch: {lines[5589]!r}"
assert "fitAddon" in lines[5601], f"L5602 mismatch: {lines[5601]!r}"
assert "setTimeout(function() { try { fitAddon.fit()" in lines[5606], f"L5607 mismatch: {lines[5606]!r}"

# --- FIX 1: Terminal config block (L5590-5600 -> 0-idx 5589-5599) ---
# Replace the whole 11-line block with a fresh one that has rows/cols/scrollback
new_terminal_block = (
    "    var term = new Terminal({" + eol +
    "        cursorBlink: true," + eol +
    "        rows: 24," + eol +
    "        cols: 80," + eol +
    "        scrollback: 2000," + eol +
    "        fontSize: 12," + eol +
    "        fontFamily: 'Consolas, monospace'," + eol +
    "        theme: {" + eol +
    "            background: '#000000'," + eol +
    "            foreground: '#ff9d00'," + eol +
    "            cursor: '#ff9d00'," + eol +
    "            selection: '#333333'" + eol +
    "        }" + eol +
    "    });" + eol
)
# Verify L5600 is the closing "});"
assert lines[5599].strip() == "});", f"L5600 mismatch: {lines[5599]!r}"

# --- FIX 2: L5602 triple assignment -> single ---
new_loadaddon = "    term.loadAddon(fitAddon); window.termFitAddon = fitAddon; window.term = term;" + eol

# --- FIX 3: L5607 fit timing (fit after 500ms is fine, but ensure dimensions are real) ---
new_fit = "    setTimeout(function() { try { if (termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} }, 750);" + eol

# --- Apply all three (do them bottom-up so indices don't shift) ---
lines[5606] = new_fit          # L5607
lines[5601] = new_loadaddon    # L5602
lines[5589:5600] = [new_terminal_block]  # L5590-5600 (11 lines -> 1)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Terminal config, loadAddon, fit timing all patched")
print(f"Line count: {len(lines)}")
