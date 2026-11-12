import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[3647].endswith("\r\n") else "\n"

# Verify line 3648 is the close button span
assert "terminal-close-btn" in lines[3647], f"L3648 mismatch: {lines[3647]!r}"

lines[3647] = '        <span id="terminal-close-btn" onclick="document.getElementById(\'terminal-panel\').style.display=\'none\'" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>' + eol

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH OK: Inline onclick on close button")
