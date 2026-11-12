import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the resize handler and add a print
for i, line in enumerate(lines):
    if "def handle_terminal_resize(data):" in line:
        # Insert print after the function definition
        for j in range(i, min(len(lines), i + 10)):
            if "terminal_process.setwinsize" in lines[j]:
                # Insert print BEFORE setwinsize
                lines.insert(j, f"        print(f'BACKEND RESIZE: rows={{data.get(\"rows\")}}, cols={{data.get(\"cols\")}}')" + ("\r\n" if lines[j].endswith("\r\n") else "\n"))
                print(f"Added debug print at line {j+1}")
                break
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("DONE")
