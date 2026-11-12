import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[11365].endswith("\r\n") else "\n"

# 1. Add scrollback disable inside the Ctrl+C block (line 11370 is 'return;')
assert "return;" in lines[11369], f"L11370 mismatch: {lines[11369]!r}"
lines.insert(11369, "            if (window.term) { window.term.options.scrollback = 0; }" + eol)

# 2. Re-enable scrollback when pressing Enter (line 11372 is 'if (data === '\r')')
# It shifted +1 due to the insert above, so it's now index 11372
assert "if (data === '\\r')" in lines[11372], f"L11373 mismatch: {lines[11372]!r}"
lines.insert(11373, "            if (window.term) { window.term.options.scrollback = 2000; }" + eol)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Added scrollback control to Ctrl+C and Enter")
