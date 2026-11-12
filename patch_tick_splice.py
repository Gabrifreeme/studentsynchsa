import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11279].endswith("\r\n") else "\n"

# Verify (1-indexed 11280-11284 -> 0-indexed 11279-11283)
assert "socket.on('terminal_output'" in lines[11279], f"L11280 mismatch: {lines[11279]!r}"
assert lines[11283].strip() == "});", f"L11284 mismatch: {lines[11283]!r}"

new_block = (
    "    socket.on('terminal_output', function(data) {" + eol +
    "        // Detect heartbeat frames and add a green tick" + eol +
    "        if (/\\[SERVER\\]\\s*[\\/_|\\\\]/.test(data)) {" + eol +
    "            data = data.replace(/(\\[SERVER\\]\\s*[\\/_|\\\\])/, '$1 \\x1b[32m\\u2705\\x1b[0m');" + eol +
    "        }" + eol +
    "        term.write(data);" + eol +
    "    });" + eol
)

new_lines = lines[:11279] + [new_block] + lines[11284:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: terminal_output handler patched at lines 11280-11284")
