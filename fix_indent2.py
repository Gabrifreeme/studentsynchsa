import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[15308].endswith("\r\n") else "\n"

# Verify (0-indexed 15308-15312)
assert "xterm-256color" in lines[15308], f"L15309 mismatch: {lines[15308]!r}"
assert "TERM'] = 'dumb'" in lines[15309], f"L15310 mismatch: {lines[15309]!r}"
assert "PSReadLine" in lines[15310], f"L15311 mismatch: {lines[15310]!r}"
assert "ps_cmd = " in lines[15311], f"L15312 mismatch: {lines[15311]!r}"
assert "PtyProcess.spawn" in lines[15312], f"L15313 mismatch: {lines[15312]!r}"

new_block = (
    "    os.environ['TERM'] = 'dumb'" + eol +
    "    ps_cmd = 'powershell.exe -NoLogo -NoProfile -NonInteractive -Command \"Remove-Module PSReadLine -ErrorAction SilentlyContinue; Set-PSReadLineOption -EditMode Windows\"'" + eol +
    "    terminal_process = PtyProcess.spawn(ps_cmd)" + eol
)

new_lines = lines[:15308] + [new_block] + lines[15313:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Fixed indentation, removed duplicate TERM line")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
