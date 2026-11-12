import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the heartbeat write line
for i, line in enumerate(lines):
    if "sys.stdout.write('\\b' + frames[idx])" in line:
        eol = "\r\n" if line.endswith("\r\n") else "\n"
        indent = line[:len(line) - len(line.lstrip())]
        
        # Replace with direct queue put (CR to overwrite, green tick, no newline)
        new_heartbeat = (
            indent + "_LOG_QUEUE.put('\\r\\x1b[33m[SERVER] ' + frames[idx] + ' \\x1b[32m\\u2705\\x1b[0m')" + eol
        )
        lines[i] = new_heartbeat
        print(f"SPLICE OK: Heartbeat now writes directly to queue at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
