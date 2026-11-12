import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add !important to the terminal panel CSS to override ANY inline flex
css = """
<style>
#terminal-panel[style*="display: none"], #terminal-panel.closed {
    display: none !important;
}
</style>
"""
if "#terminal-panel[style*=\"display: none\"]" not in html:
    html = html.replace("</head>", css + "\n</head>", 1)

# 2. Change the close functions to use the hidden attribute AND display:none
js = """
<script>
window.closeAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (p) { 
        p.style.display = 'none'; 
        p.style.setProperty('display', 'none', 'important');
        p.setAttribute('hidden', 'true'); 
    }
};
window.toggleAceTerminal = function() {
    var p = document.getElementById('terminal-panel');
    if (!p) return;
    if (p.hasAttribute('hidden') || p.style.display === 'none') {
        p.removeAttribute('hidden');
        p.style.removeProperty('display');
        p.style.display = 'flex';
        if (window.openAceTerminal) window.openAceTerminal();
    } else {
        window.closeAceTerminal();
    }
};
</script>
"""
if "p.style.setProperty('display', 'none', 'important')" not in html:
    html = html.replace("</body>", js + "\n</body>")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("PATCH COMPLETE: Brute force hidden attribute + !important")
