import io, re

html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Nuke any old #terminal-output CSS and inject a strictly-sized version
html = re.sub(r"#terminal-output\s*\{[^}]*\}", "", html)

clean_css = """
/* TERMINAL CONTAINER FIX */
#terminal-output {
    display: block !important;
    flex: 1 !important;
    min-height: 0 !important;
    width: 100% !important;
    height: 100% !important;
    overflow: hidden !important;
    padding: 4px !important;
    margin: 0 !important;
    background: #000 !important;
    position: relative !important;
}
.xterm { width: 100% !important; height: 100% !important; }
.xterm-viewport { overflow-y: scroll !important; }
"""
html = html.replace("</style>", clean_css + "\n</style>", 1)

# 2. Fix the terminal-panel flex so it uses min-height
html = html.replace(
    'style="display: none; flex-direction: column; height: 300px;',
    'style="display: none; flex-direction: column; height: 300px; min-height: 300px;'
)

# 3. Force FitAddon.fit() to run AFTER a small delay to ensure layout is settled
if "setTimeout(function() { try { if (termContainer.offsetWidth" in html:
    html = html.replace(
        "setTimeout(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} }, 50);",
        "setTimeout(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} }, 250);"
    )
elif "requestAnimationFrame(function() { try { if (termContainer.offsetWidth" in html:
    # In case previous patch replaced it with rAF
    html = html.replace(
        "requestAnimationFrame(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} });",
        "setTimeout(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} }, 250);"
    )

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("FRONTEND: Fixed flex heights and added 250ms delayed fit.")
