import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Update the terminal_output handler to respect the flag
for i, line in enumerate(lines):
    if "socket.on('terminal_output'" in line:
        # Insert the check right after the function line
        lines.insert(i + 1, "        if (window._blockOutput) { return; }" + eol)
        print(f"INJECTED: Output block check at line {i+2}")
        break

# 2. Update the Ctrl+C block to SET the flag
for i, line in enumerate(lines):
    if "data === '\\x03'" in line:
        # Find the end of the Ctrl+C block (look for the return;)
        for j in range(i, i + 15):
            if "return;" in lines[j]:
                lines.insert(j, "            window._blockOutput = true;" + eol)
                print(f"INJECTED: Set _blockOutput on Ctrl+C at line {j+1}")
                break
        break

# 3. Update the Enter block to CLEAR the flag
for i, line in enumerate(lines):
    if "data === '\\r'" in line:
        lines.insert(i + 1, "            window._blockOutput = false;" + eol)
        print(f"INJECTED: Clear _blockOutput on Enter at line {i+2}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE")
