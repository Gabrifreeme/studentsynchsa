import io

# --- BACKEND FIX: Clear PTY buffer on connect ---
py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# Find the connect handler and add a read() loop to flush the buffer
old_connect = """    if not terminal_process or not terminal_process.isalive():
        # Spawn PowerShell on Windows"""
new_connect = """    if not terminal_process or not terminal_process.isalive():
        # Spawn PowerShell on Windows"""

if "terminal_process.read(1024)" in py and "while True:" not in py:
    # Add a buffer flush inside the connect function
    py = py.replace(
        "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')",
        "terminal_process = PtyProcess.spawn('powershell.exe -NoLogo -NoProfile -NonInteractive')\n        # Flush any ghost input left in the PTY buffer from previous sessions\n        try:\n            import time\n            time.sleep(0.1)\n            while True:\n                if not terminal_process.isalive(): break\n                import select\n                r, _, _ = select.select([terminal_process.fd], [], [], 0)\n                if r:\n                    terminal_process.read(1024)\n                else:\n                    break\n        except Exception:\n            pass"
    )
    print("BACKEND: Flushed PTY buffer on connect")

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.write(py)


# --- FRONTEND FIX: Force 24 rows and delay fit ---
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Change xterm initialization to start with 24 rows
html = html.replace(
    "var term = new Terminal({",
    "var term = new Terminal({\n        rows: 24,"
)

# Ensure the fit happens after a solid 100ms (give browser time to layout)
html = html.replace(
    "setTimeout(function() {\n        try {\n            fitAddon.fit();",
    "setTimeout(function() {\n        try {\n            if (termContainer.offsetHeight > 0) { fitAddon.fit(); }"
)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Forced 24-row init and delayed fit")
print("PATCH COMPLETE")
