import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[15278].endswith("\r\n") else "\n"

# Verify boundaries (1-indexed 15279 and 15293 -> 0-indexed 15278 and 15292)
assert "try:" in lines[15278], f"L15279 mismatch: {lines[15278]!r}"
assert "pass" in lines[15292], f"L15293 mismatch: {lines[15292]!r}"

# Replace lines 15279-15293 (0-idx 15278-15292) with clean block
new_block = (
    "        try:" + eol +
    "            # Handle Backspace (DEL/BS) cleanly" + eol +
    "            if data in ('\\x7f', '\\x08'):" + eol +
    "                terminal_process.write('\\b \\b')" + eol +
    "            elif data == '\\r':" + eol +
    "                terminal_process.write('\\r\\n')" + eol +
    "            else:" + eol +
    "                terminal_process.write(data)" + eol +
    "        except Exception:" + eol +
    "            pass" + eol
)

new_lines = lines[:15278] + [new_block] + lines[15293:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print(f"SPLICE OK: Replaced lines 15279-15293")
print(f"Line count: {len(lines)} -> {len(new_lines)}")
