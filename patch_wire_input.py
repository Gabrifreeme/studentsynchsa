import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Remove any existing cmd-input wiring first
import re
html = re.sub(r"<script>\s*document\.addEventListener\('DOMContentLoaded', function\(\) \{\s*setTimeout\(function\(\) \{\s*var inp = document\.getElementById\('terminal-cmd-input'\).*?</script>", "", html, flags=re.DOTALL)

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
                    var cmd = inp.value.trim();
                    if (!cmd) return;
                    if (window.term && window.termSocket) {
                        window.term.write(cmd + '\\r\\n');
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

html = html.replace("</body>", js_block + "\n</body>")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE: Wired cmd input")
