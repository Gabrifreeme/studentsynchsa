p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
lines = open(p, 'r', encoding='utf-8').read().splitlines()

# Find the line with "var term = new Terminal({"
start_line = -1
for i, line in enumerate(lines):
    if 'var term = new Terminal(' in line:
        start_line = i
        break

if start_line == -1:
    print("TERMINAL INIT NOT FOUND")
    exit()

# Find the line with "document.addEventListener('DOMContentLoaded'" just before this init
# That's where we wrap
wrap_start = -1
for i in range(start_line, -1, -1):
    if "addEventListener('DOMContentLoaded'" in lines[i]:
        wrap_start = i
        break

if wrap_start == -1:
    print("DOMCONTENTLOADED NOT FOUND")
    exit()

# Find the "});" that closes the DOMContentLoaded after start_line
# We count braces from wrap_start to find the match
brace_count = 0
end_line = -1
for i in range(wrap_start, len(lines)):
    for char in lines[i]:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
    if brace_count == 0 and i > wrap_start + 2:
        end_line = i
        break

if end_line == -1:
    print("END OF DOMCONTENTLOADED NOT FOUND")
    exit()

print(f"DOMContentLoaded block: lines {wrap_start+1} to {end_line+1}")

# Extract the inner content (between the opening { and closing })
# We'll create a new function called initAceTerminal that wraps everything inside

# Delete the old DOMContentLoaded wrapper lines
del lines[end_line]  # Remove the closing "});"
del lines[wrap_start]  # Remove the "document.addEventListener('DOMContentLoaded', function() {"

# Now insert the function wrapper at the same location
lines.insert(wrap_start, "window.initAceTerminal = function() {")
lines.insert(end_line, "};")  # Add closing

# Now wire the panel display toggles to call initAceTerminal
for i, line in enumerate(lines):
    if "document.getElementById('terminal-panel').style.display = 'flex'" in line and 'onclick' not in line:
        # This is the toolbar button onclick - replace the whole line
        lines[i] = line.replace(
            "document.getElementById('terminal-panel').style.display = 'flex'",
            "if (window.initAceTerminal) window.initAceTerminal(); document.getElementById('terminal-panel').style.display = 'flex'"
        )
    elif "document.getElementById('terminal-panel').style.display = 'flex'" in line:
        # Inside an inline onclick attribute
        lines[i] = line.replace(
            "document.getElementById('terminal-panel').style.display = 'flex'",
            "document.getElementById('terminal-panel').style.display = 'flex'; if (window.initAceTerminal) window.initAceTerminal()"
        )
    elif 'document.getElementById("terminal-panel").style.display = "flex"' in line:
        # Inside JS with double quotes
        lines[i] = line.replace(
            'document.getElementById("terminal-panel").style.display = "flex"',
            'document.getElementById("terminal-panel").style.display = "flex"; if (window.initAceTerminal) window.initAceTerminal()'
        )

open(p, 'w', encoding='utf-8').write('\n'.join(lines))
print("TERMINAL SAFELY WRAPPED AND WIRED")