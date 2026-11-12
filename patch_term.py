import re, io, sys

path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
i = 0
removed_input = False
while i < len(lines):
    line = lines[i]
    # Remove legacy terminal-input <input> line
    if not removed_input and 'id="terminal-input"' in line and '<input' in line:
        removed_input = True
        i += 1
        continue
    out.append(line)
    i += 1

text = "".join(out)

# Replace the after-open setTimeout with safe fit
text = text.replace(
    "setTimeout(function() { try { fitAddon.fit(); term.focus(); } catch(e) {} }, 500);",
    "setTimeout(function() { try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); } term.focus(); } catch(e) {} }, 50);"
)

# Replace all bare fitAddon.fit() / window.termFitAddon.fit() calls with guarded version
text = text.replace(
    "try { fitAddon.fit(); socket.emit('terminal_resize', { rows: term.rows, cols: term.cols }); } catch(e) {}",
    "try { if (termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) { fitAddon.fit(); socket.emit('terminal_resize', { rows: term.rows, cols: term.cols }); } } catch(e) {}"
)

# Remove duplicate ResizeObserver block (second identical occurrence)
block = """    // Force fit on any resize
    if (window.ResizeObserver) {
        var resizeObs = new ResizeObserver(function() {
            if (window.termFitAddon) {
                try { window.termFitAddon.fit(); } catch(e) {}
            }
        });
        resizeObs.observe(termContainer);
    }
"""
# Keep only first occurrence
idx1 = text.find(block)
if idx1 != -1:
    idx2 = text.find(block, idx1 + len(block))
    if idx2 != -1:
        text = text[:idx2] + text[idx2+len(block):]

# Clean up triple assignment on line 5602
text = text.replace(
    "term.loadAddon(fitAddon); window.termFitAddon = fitAddon; window.term = term; window.termFitAddon = fitAddon; window.term = term; window.termFitAddon = fitAddon;",
    "term.loadAddon(fitAddon); window.termFitAddon = fitAddon; window.term = term;"
)

# Guard ResizeObserver callback
text = text.replace(
    "if (window.termFitAddon) {\n                try { window.termFitAddon.fit(); } catch(e) {}\n            }",
    "if (window.termFitAddon && termContainer.offsetWidth > 0 && termContainer.offsetHeight > 0) {\n                try { window.termFitAddon.fit(); } catch(e) {}\n            }"
)

with io.open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("PATCH OK: removed_input =", removed_input)
