import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# 1. Remove the duplicate sys.stdout = SimpleLogger lines, keep only one
stdout_indices = []
for i, line in enumerate(lines):
    if "sys.stdout = SimpleLogger(sys.stdout, _LOG_QUEUE)" in line:
        stdout_indices.append(i)

if len(stdout_indices) > 1:
    # Keep the first one, remove the rest
    for i in reversed(stdout_indices[1:]):
        del lines[i]
    print(f"BACKEND: Removed {len(stdout_indices)-1} duplicate SimpleLogger wrappers")

# 2. Fix the write method to NOT send ANSI to the console
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "def write(self, message):" in line:
        start_idx = i
    if start_idx is not None and "self.queue.put(msg_text)" in line:
        end_idx = i
        break

assert start_idx is not None and end_idx is not None, "Could not find write method"

eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"
indent = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]

# Replace the whole block with a clean version
new_block = (
    "    def write(self, message):" + eol +
    "        try:" + eol +
    "            msg_text = message" + eol +
    "            if '* Running on http://127.0.0.1:5000' in msg_text:" + eol +
    "                msg_text = msg_text.rstrip() + ' ✅\\n'" + eol +
    "            elif 'ntfy.sh' in msg_text:" + eol +
    "                msg_text = msg_text.rstrip() + ' ⭐\\n'" + eol +
    "            else:" + eol +
    "                import re" + eol +
    "                match = re.search(r'\\s(\\d{3})\\s', msg_text)" + eol +
    "                if match:" + eol +
    "                    status = match.group(1)" + eol +
    "                    if status in ('200', '201', '202', '204'):" + eol +
    "                        msg_text = msg_text.rstrip() + ' 😊\\n'" + eol +
    "                    elif status.startswith(('4', '5')):" + eol +
    "                        msg_text = msg_text.rstrip() + ' ❌\\n'" + eol +
    "" + eol +
    "            # 1. Write CLEAN text to the console (no ANSI colors)" + eol +
    "            self.original.write(msg_text)" + eol +
    "            if hasattr(self, 'queue') and self.queue:" + eol +
    "                # 2. Check if this is a heartbeat frame" + eol +
    "                stripped = msg_text.strip()" + eol +
    "                if stripped and stripped[-1] in ('_', '/', '|', '\\\\'):" + eol +
    "                    # Add ANSI green tick ONLY to the queue (frontend)" + eol +
    "                    msg_text = msg_text.rstrip() + ' \\x1b[32m\\u2705\\x1b[0m'" + eol +
    "                self.queue.put(msg_text)" + eol +
    "        except Exception:" + eol +
    "            pass" + eol
)

new_lines = lines[:start_idx] + [new_block] + lines[end_idx+1:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Fixed write method at lines {start_idx+1}-{end_idx+1}")
