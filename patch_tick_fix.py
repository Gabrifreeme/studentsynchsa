import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the HEARTBEAT_TICK block
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "# HEARTBEAT_TICK" in line:
        start_idx = i
    if start_idx is not None and "self.queue.put(msg_text)" in line:
        end_idx = i
        break

assert start_idx is not None and end_idx is not None, "Could not find HEARTBEAT_TICK block"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"
indent = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]

# Replace the whole block: write to console FIRST (clean), then tick for queue
new_block = (
    indent + "self.original.write(msg_text)" + eol +
    indent + "if hasattr(self, 'queue') and self.queue:" + eol +
    indent + "    # Check if this is a heartbeat frame (last char is one of _ / | \\\\)" + eol +
    indent + "    stripped = msg_text.strip()" + eol +
    indent + "    if stripped and stripped[-1] in ('_', '/', '|', '\\\\'):" + eol +
    indent + "        msg_text = msg_text.rstrip() + ' \\x1b[32m\\u2705\\x1b[0m'" + eol +
    indent + "    self.queue.put(msg_text)" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx+1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Fixed tick block, console clean, queue gets tick")
