import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11319].endswith("\r\n") else "\n"

# Verify (1-indexed 11318 -> 0-indexed 11317)
assert "socket.emit('terminal_resize', dims)" in lines[11317], f"L11318 mismatch: {lines[11317]!r}"
assert lines[11319].strip() == "});", f"L11320 mismatch: {lines[11319]!r}"

# Insert auto-tail command before the closing });
insert = (
    "" + eol +
    "        // Auto-tail server log" + eol +
    "        setTimeout(function() {" + eol +
    "            socket.emit('terminal_input', 'Get-Content server.log -Wait -Tail 20\\r');" + eol +
    "        }, 1000);" + eol
)

lines.insert(11319, insert)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"INJECTED: Auto-tail command at line 11320")
