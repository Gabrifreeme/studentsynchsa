import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[7276].endswith("\r\n") else "\n"

# Verify (1-indexed 7277, 7280 -> 0-indexed 7276, 7279)
assert 'id="terminal-panel"' in lines[7276], f"L7277 mismatch: {lines[7276]!r}"
assert 'id="terminal-output"' in lines[7279], f"L7280 mismatch: {lines[7279]!r}"

# Insert header right after terminal-panel opening div (before terminal-output)
header_block = (
    "" + eol +
    '        <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: #111; border-bottom: 1px solid #333;">' + eol +
    '            <span style="color: #ff9d00; font-weight: bold; font-family: monospace; font-size: 12px; white-space: nowrap;">ACEsi Terminal</span>' + eol +
    '            <input id="terminal-cmd-input" type="text" placeholder="Type command and press Enter..." style="flex: 1; margin: 0 15px; background: #000; color: #ff9d00; border: 1px solid #555; padding: 2px 8px; font-family: monospace; font-size: 12px; outline: none;" autocomplete="off">' + eol +
    '            <div style="display: flex; gap: 15px; white-space: nowrap;">' + eol +
    '                <span id="terminal-min-btn" onclick="window.toggleMinimize()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">–</span>' + eol +
    '                <span id="terminal-close-btn" onclick="window.closeAceTerminal()" style="color: #ff9d00; cursor: pointer; font-weight: bold; font-family: monospace;">X Close</span>' + eol +
    '            </div>' + eol +
    '        </div>' + eol
)

# Insert at line 7278 (0-indexed 7277, right before line 7280)
lines.insert(7277, header_block)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Injected header with cmd input at line 7278")
