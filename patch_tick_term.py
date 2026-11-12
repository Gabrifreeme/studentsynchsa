import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# 1. Revert the broken console heartbeat line
for i, line in enumerate(lines):
    if "sys.stdout.write('\\b' + frames[idx] + ' \\x1b[32m\\u2705\\x1b[0m')" in line:
        lines[i] = line.replace("sys.stdout.write('\\b' + frames[idx] + ' \\x1b[32m\\u2705\\x1b[0m')", "sys.stdout.write('\\b' + frames[idx])")
        print(f"REVERTED: Fixed console heartbeat at line {i+1}")
        break

# 2. Add green tick to SimpleLogger.write (frontend output)
for i, line in enumerate(lines):
    if "def write(self, message):" in line:
        # Find the line inside write that does self.queue.put
        for j in range(i, i + 30):
            if "self.queue.put(msg_text)" in lines[j]:
                # Check if we already added the tick logic
                if "HEARTBEAT_TICK" not in lines[j-1] and "HEARTBEAT_TICK" not in lines[j]:
                    # Insert the tick logic right before queue.put
                    eol = "\r\n" if lines[j].endswith("\r\n") else "\n"
                    indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                    
                    # A simple check: if the message is a single heartbeat char, add the tick
                    tick_logic = (
                        indent + "# HEARTBEAT_TICK" + eol +
                        indent + "if len(msg_text.strip()) == 1 and msg_text.strip() in ['_', '/', '|', '\\\\']:" + eol +
                        indent + "    msg_text = msg_text + ' \\x1b[32m\\u2705\\x1b[0m'" + eol
                    )
                    lines.insert(j, tick_logic)
                    print(f"INJECTED: Green tick logic at line {j+1}")
                break
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE")
