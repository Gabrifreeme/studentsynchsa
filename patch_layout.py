import io

path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Fix the CSS rule at line 469 (remove flex/alignment weirdness)
old_css = "#terminal-output { display: block; width: 100%; height: 100%;"
new_css = "#terminal-output { position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
if old_css in text:
    text = text.replace(old_css, new_css)
    print("CSS: Forced absolute positioning for terminal")
else:
    print("CSS: WARNING - Could not find the terminal-output CSS rule")

# 2. Fix the inline JS styles inside initAceTerminal (line ~5584)
old_js_css = """    termContainer.style.padding = '0';
    termContainer.style.background = '#000';
    termContainer.style.display = 'block';
    termContainer.style.width = '100%';
    termContainer.style.height = '100%';"""
new_js_css = """    termContainer.style.padding = '0';
    termContainer.style.background = '#000';
    termContainer.style.display = 'block';
    termContainer.style.width = '100%';
    termContainer.style.height = '100%';
    termContainer.style.position = 'relative';"""
if old_js_css in text:
    text = text.replace(old_js_css, new_js_css)
    print("JS: Added relative positioning to termContainer")

# 3. Fix the padding injection AFTER term.open (line ~5605)
old_open_pad = """    term.open(termContainer);
    termContainer.style.padding = '4px';
    termContainer.style.textAlign = 'left';"""
new_open_pad = """    term.open(termContainer);
    termContainer.style.padding = '4px';
    termContainer.style.textAlign = 'left';
    
    // Force xterm element to top-left
    var xtermEl = termContainer.querySelector('.xterm');
    if (xtermEl) { xtermEl.style.position = 'absolute'; xtermEl.style.top = '0'; xtermEl.style.left = '0'; }"""
if old_open_pad in text:
    text = text.replace(old_open_pad, new_open_pad)
    print("JS: Forced .xterm element to top-left")

# 4. Fix the terminal panel container (line 3627)
old_panel = """<div id="terminal-panel" style="display: none; flex-direction: column; height: 300px; background: #00"""
new_panel = """<div id="terminal-panel" style="display: none; flex-direction: column; height: 300px; position: relative; background: #00"""
if old_panel in text:
    text = text.replace(old_panel, new_panel)
    print("HTML: Added position:relative to terminal-panel")

with io.open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("PATCH COMPLETE")
