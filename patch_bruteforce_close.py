import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

js = """
<script>
// BRUTEFORCE CLOSE BUTTON FIX
document.addEventListener('mousedown', function(e) {
    var el = e.target;
    while (el && el !== document.body) {
        if (el.textContent && el.textContent.trim() === 'X Close') {
            console.log('CLOSE CLICKED');
            var panel = document.getElementById('terminal-panel');
            if (panel) panel.style.display = 'none';
            return;
        }
        el = el.parentElement;
    }
});
</script>
"""
if "BRUTEFORCE CLOSE BUTTON FIX" not in html:
    html = html.replace("</body>", js + "\n</body>")
    print("JS: Injected bruteforce close listener")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)

print("PATCH COMPLETE")
