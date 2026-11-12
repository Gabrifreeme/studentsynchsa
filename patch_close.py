import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Find the Close button in the HTML and clean it up
for i, line in enumerate(lines):
    if "X Close" in line and "<span" in line:
        lines[i] = '        <span id="terminal-close-btn" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>' + eol
        print(f"HTML: Cleaned up Close button at line {i+1}")
        break

# 2. Inject the JS event listener at the very end of the body
js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    var closeBtn = document.getElementById('terminal-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('terminal-panel').style.display = 'none';
        });
    }
});
</script>
"""
if "terminal-close-btn" not in "\n".join(lines[:100]): # Make sure we don't double inject
    html = "".join(lines)
    html = html.replace("</body>", js + "\n</body>")
    lines = html.splitlines(keepends=True)
    print("JS: Injected Close button event listener")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
