import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[15310].endswith("\r\n") else "\n"

# Verify (1-indexed 15311-15313 -> 0-indexed 15310-15312)
assert "PSReadLine" in lines[15310], f"L15311 mismatch: {lines[15310]!r}"
assert "ps_cmd" in lines[15311], f"L15312 mismatch: {lines[15311]!r}"
assert "PtyProcess.spawn" in lines[15312], f"L15313 mismatch: {lines[15312]!r}"
# Verify L15310 is the duplicate TERM line we want to remove
assert "os.environ['TERM'] = 'xterm-256color'" in lines[15309], f"L15310 mismatch: {lines[15309]!r}"

# Replace lines 15310-15313 (0-indexed 15309-15312) with clean version
# Remove the duplicate TERM='xterm-256color' (15310), keep 'dumb', fix indentation
new_block = (
    "    # Spawn fresh PowerShell" + eol +
    "    os.environ['TERM'] = 'dumb'" + eol +
    "    ps_cmd = 'powershell.exe -NoLogo -NoProfile -NonInteractive -Command \"Remove-Module PSReadLine -ErrorAction SilentlyContinue; Set-PSReadLineOption -EditMode Windows\"'" + eol +
    "    terminal_process = PtyProcess.spawn(ps_cmd)" + eol
)

# Also need to remove L15308 "    # Spawn fresh PowerShell" duplicate and L15309 "# os.environ['TERM'] = 'xterm-256color'"
new_lines = lines[:15307] + [new_block] + lines[15313:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Fixed indentation, removed duplicate TERM line")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
