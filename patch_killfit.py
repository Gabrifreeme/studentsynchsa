import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Locate and modify the new Terminal() block (find "var term = new Terminal({")
term_line_idx = None
for i, line in enumerate(lines):
    if "var term = new Terminal({" in line:
        term_line_idx = i
        break

assert term_line_idx is not None, "Could not find 'new Terminal({' line"

# Inject rows and cols right after the opening brace
lines[term_line_idx] = lines[term_line_idx].replace("{", "{\n        rows: 24,\n        cols: 80,", 1)
print(f"JS: Forced rows=24 cols=80 at line {term_line_idx+1}")

# 2. Remove ALL fitAddon.fit() calls
count_removed = 0
for i in range(len(lines) - 1, -1, -1):
    if "fitAddon.fit()" in lines[i] or "window.termFitAddon.fit()" in lines[i]:
        # Check if it's part of a larger line or standalone
        if "setTimeout" in lines[i]:
            # Replace the whole setTimeout with a simple focus
            lines[i] = "    setTimeout(function() { try { term.focus(); } catch(e) {} }, 500);" + eol
            count_removed += 1
        else:
            # Remove the line entirely
            del lines[i]
            count_removed += 1
print(f"JS: Removed {count_removed} fitAddon.fit() calls")

# 3. Remove the FitAddon instantiation
for i in range(len(lines) - 1, -1, -1):
    if "var fitAddon = new FitAddon.FitAddon();" in lines[i]:
        del lines[i]
        print(f"JS: Removed FitAddon instantiation at line {i+1}")
        break

# 4. Remove the loadAddon line
for i in range(len(lines) - 1, -1, -1):
    if "term.loadAddon(fitAddon)" in lines[i]:
        lines[i] = "" + eol
        print(f"JS: Neutralized loadAddon at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
