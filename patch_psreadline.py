import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the spawn line
spawn_idx = None
for i, line in enumerate(lines):
    if "PtyProcess.spawn(" in line and "powershell" in line:
        spawn_idx = i
        break

assert spawn_idx is not None, "Could not find PowerShell spawn line"

eol = "\r\n" if lines[spawn_idx].endswith("\r\n") else "\n"

# Replace the spawn line with a version that disables PSReadLine
new_spawn = (
    "    os.environ['TERM'] = 'dumb'" + eol +
    "    ps_cmd = 'powershell.exe -NoLogo -NoProfile -Command \"Remove-Module PSReadLine -ErrorAction SilentlyContinue\"'" + eol +
    "    terminal_process = PtyProcess.spawn(ps_cmd)" + eol
)

# Find where the os.environ['TERM'] line was, if it exists, remove it so we don't duplicate
term_idx = None
for i in range(max(0, spawn_idx - 3), spawn_idx):
    if "os.environ['TERM']" in lines[i]:
        term_idx = i
        break

# If TERM line exists, replace both lines
if term_idx is not None:
    lines[term_idx:spawn_idx + 1] = [new_spawn]
else:
    lines[spawn_idx] = new_spawn

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"PATCH COMPLETE: PSReadLine disabled, spawn fixed at line {spawn_idx+1}")
