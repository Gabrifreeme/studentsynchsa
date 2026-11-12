import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Delete the legacy terminal-input block (lines 7308-7312, 0-indexed 7307-7311)
# Verify first
assert 'id="terminal-input"' in lines[7309], f"L7310 mismatch: {lines[7309]!r}"

# Delete lines 7308-7312 (the whole div containing the input)
# 0-indexed 7307 to 7311 (inclusive)
del lines[7307:7312]

# 2. Inject the paste handler JS at end of body
paste_js = (
    "<script>" + eol +
    "document.addEventListener('DOMContentLoaded', function() {" + eol +
    "    setTimeout(function() {" + eol +
    "        var btn = document.getElementById('terminal-paste-btn');" + eol +
    "        if (btn && !btn._pasteWired) {" + eol +
    "            btn._pasteWired = true;" + eol +
    "            btn.addEventListener('click', function() {" + eol +
    "                var ta = document.createElement('textarea');" + eol +
    "                ta.style.position = 'fixed';" + eol +
    "                ta.style.left = '-9999px';" + eol +
    "                document.body.appendChild(ta);" + eol +
    "                ta.focus();" + eol +
    "                try { document.execCommand('paste'); } catch(e) { console.warn('paste execCommand failed:', e); }" + eol +
    "                var text = ta.value;" + eol +
    "                document.body.removeChild(ta);" + eol +
    "                if (text && window.term) {" + eol +
    "                    if (typeof window._aceBuf !== 'undefined') { window._aceBuf += text; }" + eol +
    "                    window.term.write(text);" + eol +
    "                }" + eol +
    "            });" + eol +
    "        }" + eol +
    "    }, 1000);" + eol +
    "});" + eol +
    "</script>" + eol
)

# Find last </body>
for i in range(len(lines) - 1, -1, -1):
    if "</body>" in lines[i]:
        lines.insert(i, paste_js)
        print(f"JS: Paste handler injected before </body> at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"PATCH COMPLETE: {len(lines)} lines (deleted legacy input, added paste handler)")
