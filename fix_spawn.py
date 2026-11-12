import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find and replace the broken spawn block
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "os.environ['TERM'] = 'dumb'" in line:
        start_idx = i
    if start_idx is not None and "terminal_process = PtyProcess.spawn(ps_cmd)" in line:
        end_idx = i
        break

assert start_idx is not None, "Could not find TERM=dumb line"
assert end_idx is not None, "Could not find PtyProcess.spawn(ps_cmd) line"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"

new_block = (
    "    os.environ['TERM'] = 'xterm-256color'" + eol +
    "    terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile')" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx + 1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Replaced broken ps_cmd with plain powershell.exe")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
