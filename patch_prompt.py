import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the Ctrl+C block and replace it
# Current lines (index 11365-11372):
# 11366: if (data === '\x03') {
# 11367:     socket.emit('terminal_input', '\x03');
# 11368:     term.write('^C\r\n');
# 11369:     window._aceBuf = '';
# 11370:     window._blockOutput = true;   (we added this)
# 11371:     if (window.term) { window.term.options.scrollback = 0; }
# 11372:     return;
# 11373: }

start_idx = None
for i, line in enumerate(lines):
    if "data === '\\x03'" in line:
        start_idx = i
        break

assert start_idx is not None, "Could not find Ctrl+C handler"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"
indent = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]

# Find the closing } of the ctrl+c block
end_idx = start_idx + 1
while end_idx < len(lines) and "return;" not in lines[end_idx]:
    end_idx += 1
# include the 'return;' and the closing '}'
end_idx += 2

new_ctrlc = (
    indent + "if (data === '\\x03') {" + eol +
    indent + "    socket.emit('terminal_input', '\\x03');" + eol +
    indent + "    term.write('^C\\r\\n');" + eol +
    indent + "    window._aceBuf = '';" + eol +
    indent + "    // Force a fresh prompt line" + eol +
    indent + "    setTimeout(function() {" + eol +
    indent + "        term.write('C:\\\\Users\\\\chris\\\\LipSyncStudent> ');" + eol +
    indent + "    }, 300);" + eol +
    indent + "    return;" + eol +
    indent + "}" + eol
)

lines[start_idx:end_idx] = [new_ctrlc]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print(f"SPLICE OK: Ctrl+C now writes a manual prompt at line {start_idx+1}")
