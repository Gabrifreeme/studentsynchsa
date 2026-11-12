import io

# --- FRONTEND FIX (ACEsi.html) ---
html_path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(html_path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Enable scrollback in xterm config
if "scrollback:" not in html:
    html = html.replace("cursorBlink: true,", "cursorBlink: true,\n        scrollback: 1000,")
    print("FRONTEND: Enabled xterm scrollback")

# 2. Fix the overflow CSS for #terminal-output
# We find the CSS block and replace overflow: hidden with overflow: auto
old_css = "#terminal-output { display: block !important; text-align: left !important; padding: 0 !important; margin: 0 !important; width: 100% !important; height: 100% !important; overflow: hidden !important; background: #000 !important; position: relative !important; }"
new_css = "#terminal-output { display: block !important; text-align: left !important; padding: 0 !important; margin: 0 !important; width: 100% !important; height: 100% !important; overflow-y: auto !important; overflow-x: hidden !important; background: #000 !important; position: relative !important; }"

if old_css in html:
    html = html.replace(old_css, new_css)
    print("FRONTEND: Changed #terminal-output overflow to auto")
else:
    # Fallback: Just try to replace overflow: hidden for that block
    html = html.replace("overflow: hidden !important; background: #000 !important; position: relative !important;", "overflow-y: auto !important; background: #000 !important; position: relative !important;")
    print("FRONTEND: Fallback applied for overflow")

# 3. Ensure the term container itself allows scrolling
html = html.replace("termContainer.style.overflow = 'hidden';", "") # Remove any JS that hides overflow

with io.open(html_path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
