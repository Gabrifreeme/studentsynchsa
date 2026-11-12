import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[5574].endswith("\r\n") else "\n"

# --- VERIFY ---
assert "document.addEventListener('DOMContentLoaded'" in lines[5574], f"L5575 mismatch: {lines[5574]!r}"
assert lines[5662].strip() == "});", f"L5663 mismatch: {lines[5662]!r}"

# --- SPLICE 1: Replace L5575 with openAceTerminal wrapper ---
lines[5574] = (
    "window.openAceTerminal = function() {" + eol +
    "    var panel = document.getElementById('terminal-panel');" + eol +
    "    if (panel) { panel.style.display = 'flex'; }" + eol +
    "    if (window.term) { try { window.term.dispose(); } catch(e) {} window.term = null; }" + eol +
    "    requestAnimationFrame(function() {" + eol +
    "        requestAnimationFrame(function() {" + eol +
    "            window.initAceTerminalFn();" + eol +
    "        });" + eol +
    "    });" + eol +
    "};" + eol +
    "window.initAceTerminalFn = function() {"
)

# --- SPLICE 2: Replace L5663 with proper function closer ---
lines[5662] = "};" + eol

# --- SPLICE 3: Fix button onclick (find the Terminal button) ---
for i in range(len(lines) - 1, -1, -1):
    if "document.getElementById('terminal-panel').style.display = 'flex'" in lines[i] and "onclick" not in lines[i]:
        # The line after a `onclick="` opener — replace its contents
        if i > 0 and 'onclick="' in lines[i-1]:
            lines[i-1] = '        onclick="window.openAceTerminal()"' + eol
            lines[i] = '        "' + eol  # close the string cleanly
            print(f"BUTTON: Fixed onclick at lines {i}-{i+1}")
            break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Wrapped in openAceTerminal, fixed button")
print(f"Line count: {len(lines)}")
