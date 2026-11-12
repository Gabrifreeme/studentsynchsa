import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the heartbeat line
for i, line in enumerate(lines):
    if "sys.stdout.write('\\r' + frames[idx])" in line:
        # Replace it with a backspace + character
        lines[i] = "                sys.stdout.write('\\b' + frames[idx])" + eol
        print(f"SPLICE OK: Changed heartbeat to backspace at line {i+1}")
        break

# Also need to make sure the queue doesn't drop the backspace character
# But actually, the SimpleLogger will just put the \b in the queue, which is fine.

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
