import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the specific line in the terminal_output handler that does the replacement
old_emit = """        // Strip all ANSI escape sequences
        clean_data = re.sub(r'\\x1b\\[[0-9;?]*[A-Za-z]|\\^\\[\\[?[0-9;]*[A-Za-z]|\\x1b[\\]P^_][^\\x07]*\\x07', '', data)"""

# This is in the backend! The frontend just does term.write(data). Wait.
# Let me check the FRONTEND raw IN logger we added.
# The frontend currently has:
# socket.on('terminal_output', function(data) {
#     term.write(data);
# });

# Actually, the issue is in the BACKEND at line 15323!
# clean_data = clean_data.replace('\r\n', '\n').replace('\r', '')

# We need to revert that.
# Let's open server.py and fix the clean_data logic.
