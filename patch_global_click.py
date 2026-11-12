import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

js = """
<script>
document.addEventListener('click', function(e) {
    if (e.target && e.target.textContent && e.target.textContent.trim() === 'X Close') {
        var p = document.getElementById('terminal-panel');
        if (p) p.style.display = 'none';
    }
});
</script>
"""
if "e.target.textContent.trim() === 'X Close'" not in html:
    html = html.replace("</body>", js + "\n</body>")
    print("JS: Injected global click interceptor for Close button")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)

print("PATCH COMPLETE")
