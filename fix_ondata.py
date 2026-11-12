import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11389].endswith("\r\n") else "\n"

# Verify (1-indexed 11390 and 11394 -> 0-indexed 11389 and 11393)
assert "term.onData(function(data)" in lines[11389], f"L11390 mismatch: {lines[11389]!r}"
assert lines[11393].strip() == "});", f"L11394 mismatch: {lines[11393]!r}"

new_block = (
    "    term.onData(function(data) {" + eol +
    "        // Handle Backspace locally so the screen updates instantly" + eol +
    "        if (data === '\\x7f' || data === '\\x08') {" + eol +
    "            term.write('\\b \\b');" + eol +
    "        }" + eol +
    "        socket.emit('terminal_input', data);" + eol +
    "    });" + eol
)

new_lines = lines[:11389] + [new_block] + lines[11394:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Replaced term.onData block at lines 11390-11394")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
