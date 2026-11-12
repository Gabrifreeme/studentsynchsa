import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Find the terminal_input handler
old_input = """        try:
            if data == '\\r':
                terminal_process.write('\\r')
            else:
                terminal_process.write(data)
        except Exception:
            pass"""

new_input = """        try:
            # Fix Backspace (DEL or BS) by sending backspace-space-backspace
            if data == '\\x7f' or data == '\\x08':
                terminal_process.write('\\b \\b')
            elif data == '\\r':
                terminal_process.write('\\r\\n')
            else:
                terminal_process.write(data)
        except Exception:
            pass"""

if old_input in py:
    py = py.replace(old_input, new_input)
    print("BACKEND: Fixed Backspace and Enter handling")
else:
    # Fallback if the exact block isn't there
    py = py.replace("terminal_process.write(data)", 
        "if data in ('\\x7f', '\\x08'): terminal_process.write('\\b \\b')\n            elif data == '\\r': terminal_process.write('\\r\\n')\n            else: terminal_process.write(data)")
    print("BACKEND: Applied fallback Backspace fix")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
