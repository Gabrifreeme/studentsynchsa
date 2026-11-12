import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the exact line where clean_data is calculated
clean_data_idx = None
for i, line in enumerate(lines):
    if "clean_data = re.sub(" in line:
        clean_data_idx = i
        break

assert clean_data_idx is not None, "Could not find clean_data line"

eol = "\r\n" if lines[clean_data_idx].endswith("\r\n") else "\n"
indent = lines[clean_data_idx][:len(lines[clean_data_idx]) - len(lines[clean_data_idx].lstrip())]

# Replace the clean_data line with one that strips CR and LF completely
# (xterm will handle line wrapping automatically)
new_line = (
    indent + "clean_data = re.sub(r'\\x1b\\[[0-9;?]*[A-Za-z]', '', data)" + eol +
    indent + "# Replace all CR and LF with empty space to stop cursor jumping" + eol +
    indent + "clean_data = clean_data.replace('\\r\\n', '\\n').replace('\\r', '')" + eol
)

lines[clean_data_idx] = new_line

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Injected CR strip at line {clean_data_idx+1}")
