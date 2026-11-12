import io

# ==========================================
# 1. FIX FRONTEND (ACEsi.html)
# ==========================================
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    # Fix CSS alignment (line 469 area)
    if "#terminal-output {" in line and "text-align" not in line:
        line = line.replace("display: block;", "display: block; text-align: left !important; padding: 0 !important; margin: 0 !important;")
    
    # Fix JS term.onData
    if "term.onData(function(data) {" in line:
        out.append(line)
        out.append("        // Intercept Enter key on the frontend for Windows PTY\n")
        out.append("        var payload = (data === '\\r') ? '\\r\\n' : data;\n")
        out.append("        socket.emit('terminal_input', payload);\n")
        continue
    
    # Skip the old socket.emit line since we replaced it above
    if "socket.emit('terminal_input', data);" in line:
        continue
        
    out.append(line)

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.writelines(out)
print("FRONTEND: Fixed onData to send \\r\\n and CSS to top-left")


# ==========================================
# 2. FIX BACKEND (server.py)
# ==========================================
py_path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(py_path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

out = []
for i, line in enumerate(lines):
    # We replace the exact lines 15272 through 15279 (0-indexed 15271 to 15278)
    if i == 15271: # @socketio.on('terminal_input')
        out.append(line)
        out.append("def handle_terminal_input(data):\n")
        out.append("    global terminal_process\n")
        out.append("    if terminal_process and terminal_process.isalive():\n")
        out.append("        try:\n")
        out.append("            # Write data directly. If it's a newline, ensure it's \\r\n")
        out.append("            if data == '\\r' or data == '\\r\\n':\n")
        out.append("                terminal_process.write('\\r\\n')\n")
        out.append("            else:\n")
        out.append("                terminal_process.write(data)\n")
        out.append("        except Exception:\n")
        out.append("            pass\n")
        continue
    
    # Skip the old function definition and body (up to line 15279)
    if 15271 < i <= 15278:
        continue
        
    out.append(line)

with io.open(py_path, "w", encoding="utf-8", newline="") as f:
    f.writelines(out)
print("BACKEND: Fixed terminal_input to handle \\r\\n explicitly")

print("PATCH COMPLETE")
