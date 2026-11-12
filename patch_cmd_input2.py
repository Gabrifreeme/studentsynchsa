import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Find the terminal header (the one with toggleMinimize)
# It currently looks like: <div style="display: flex; gap: 15px;"> ... </div>
# Let's insert a text input into that flex container.

# Find the header block
header_match = re.search(r'<div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">(.*?)</div>\s*</div>', html, re.DOTALL)

if header_match:
    # Inject a text input right before the buttons
    old_buttons = '<span id="terminal-min-btn"'
    new_input = '<input id="terminal-cmd-input" type="text" placeholder="Type command here..." style="flex: 1; margin-right: 15px; background: #000; color: #ff9d00; border: 1px solid #555; padding: 2px 8px; font-family: monospace; font-size: 12px; outline: none; display: block;" autocomplete="off">' + old_buttons
    
    html = html.replace(old_buttons, new_input)
    print("HTML: Added command input to header")
else:
    print("WARNING: Could not find terminal header")

# 2. Wire the input to send commands to the backend
js_block = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var inp = document.getElementById('terminal-cmd-input');
        if (inp && !inp._wired) {
            inp._wired = true;
            inp.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var cmd = inp.value;
                    if (!cmd.trim()) return;
                    if (window.term && window.termSocket) {
                        // Write command to terminal display
                        window.term.write(cmd + '\\r\\n');
                        // Send to backend
                        window.termSocket.emit('terminal_input', cmd);
                    }
                    inp.value = '';
                }
            });
        }
    }, 1500);
});
</script>
"""
if "terminal-cmd-input" not in html:
    html = html.replace("</body>", js_block + "\n</body>")
    print("JS: Injected input wiring")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
