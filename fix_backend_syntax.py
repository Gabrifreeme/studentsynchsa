import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# We know the error is around line 15285 (1-indexed)
# Let's find the start of the broken block
start_idx = None
for i in range(15270, 15300):
    if "# Write data directly" in lines[i] or "if data in (" in lines[i] or "terminal_process.write(data)" in lines[i]:
        start_idx = i
        break

if start_idx is None:
    print("Could not find the broken block")
else:
    eol = "\r\n" if lines[start_idx].endswith("\r\n") else "\n"
    
    # We will replace from start_idx to the end of the function (usually a few lines down)
    # Find the end of the block (the next @socketio.on or a blank line)
    end_idx = start_idx
    while end_idx < len(lines) and not lines[end_idx].startswith("@socketio") and "except Exception:" not in lines[end_idx]:
        end_idx += 1
    # Include the except block and pass
    while end_idx < len(lines) and "pass" not in lines[end_idx]:
        end_idx += 1
    end_idx += 1 # Include the pass line

    new_block = (
        "        try:" + eol +
        "            # Fix Backspace (DEL or BS) by sending backspace-space-backspace" + eol +
        "            if data in ('\\x7f', '\\x08'):" + eol +
        "                terminal_process.write('\\b \\b')" + eol +
        "            elif data == '\\r':" + eol +
        "                terminal_process.write('\\r\\n')" + eol +
        "            else:" + eol +
        "                terminal_process.write(data)" + eol +
        "        except Exception:" + eol +
        "            pass" + eol
    )
    
    new_lines = lines[:start_idx] + [new_block] + lines[end_idx:]
    
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(new_lines)
    print(f"SPLICE OK: Replaced broken input block at lines {start_idx+1}-{end_idx}")
