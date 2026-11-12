import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the current tick regex line
for i, line in enumerate(lines):
    if "data.replace(/(\\[SERVER\\]" in line or "data.replace(/(\\[SERVER\\]" in line.replace('\\', '\\\\'):
        pass
    if "data.replace(/" in line and "SERVER" in line:
        # Replace it with a version that matches the whole [SERVER] X and appends the tick
        indent = line[:len(line) - len(line.lstrip())]
        eol = "\r\n" if line.endswith("\r\n") else "\n"
        new_line = indent + "data = data.replace(/(\\[SERVER\\]\\s*[\\/_|\\\\])/, '$1 \\x1b[32m\\u2705\\x1b[0m');" + eol
        lines[i] = new_line
        print(f"SPLICE OK: Fixed regex at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE")
