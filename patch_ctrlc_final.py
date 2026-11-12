import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the Ctrl+C block
start_idx = None
for i, line in enumerate(lines):
    if "data === '\\x03'" in line:
        start_idx = i
        break

assert start_idx is not None, "Could not find Ctrl+C handler"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"
indent = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]

# Find the end of the block
end_idx = start_idx + 1
while end_idx < len(lines) and "return;" not in lines[end_idx]:
    end_idx += 1
end_idx += 2 # Include 'return;' and '}'

# Replace with a clean version: mute backend, print prompt once
new_ctrlc = (
    indent + "if (data === '\\x03') {" + eol +
    indent + "    socket.emit('terminal_input', '\\x03');" + eol +
    indent + "    term.write('^C\\r\\n');" + eol +
    indent + "    window._aceBuf = '';" + eol +
    indent + "    // Mute incoming logs for 2 seconds to let things settle" + eol +
    indent + "    window._blockOutput = true;" + eol +
    indent + "    setTimeout(function() { window._blockOutput = false; }, 2000);" + eol +
    indent + "    // Print the prompt once" + eol +
    indent + "    term.write('C:\\\\Users\\\\chris\\\\LipSyncStudent> ');" + eol +
    indent + "    return;" + eol +
    indent + "}" + eol
)

lines[start_idx:end_idx] = [new_ctrlc]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print(f"SPLICE OK: Final Ctrl+C fix applied at line {start_idx+1}")
