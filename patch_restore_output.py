import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[7303].endswith("\r\n") else "\n"

# Verify line 7304 is the header's closing </div>
assert lines[7303].strip() == "</div>", f"L7304 mismatch: {lines[7303]!r}"
# Verify line 7308 is <script>
assert "<script>" in lines[7307], f"L7308 mismatch: {lines[7307]!r}"

# Insert the terminal-output div at index 7304 (line 7305)
output_div = (
    '' + eol +
    '    <div id="terminal-output" style="flex: 1; overflow: hidden; padding: 0; margin: 0; background: #000; display: block; width: 100%; height: 100%; position: relative;"></div>' + eol
)
lines.insert(7304, output_div)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"SPLICE OK: Injected terminal-output div at line 7305")
