import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11363].endswith("\r\n") else "\n"

# Verify (1-indexed 11364, 11365 -> 0-indexed 11363, 11364)
assert "term.onData(function(data) {" in lines[11363], f"L11364 mismatch: {lines[11363]!r}"
assert "if (data === '\\r')" in lines[11364], f"L11365 mismatch: {lines[11364]!r}"

# Insert the Ctrl+C check right after term.onData(...
ctrl_c_block = (
    "        // Handle Ctrl+C explicitly" + eol +
    "        if (data === '\\x03') {" + eol +
    "            socket.emit('terminal_input', '\\x03');" + eol +
    "            term.write('^C\\r\\n');" + eol +
    "            window._aceBuf = '';" + eol +
    "            return;" + eol +
    "        }" + eol
)

lines.insert(11364, ctrl_c_block)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Injected Ctrl+C handler at line 11365")
