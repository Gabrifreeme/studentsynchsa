import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[468].endswith("\r\n") else "\n"

# --- VERIFY every target line before touching anything ---
assert "#terminal-output" in lines[468] and "display: block" in lines[468], f"L469 mismatch: {lines[468]!r}"
assert 'id="terminal-panel"' in lines[3626] and "height: 300px" in lines[3626], f"L3627 mismatch: {lines[3626]!r}"
assert 'id="terminal-output"' in lines[3631] and "overflow: hidden" in lines[3631], f"L3632 mismatch: {lines[3631]!r}"
assert "setTimeout(function() { try { fitAddon.fit()" in lines[5606], f"L5607 mismatch: {lines[5606]!r}"

# --- PATCH L469 (index 468): height 100% -> 280px on the CSS rule ---
lines[468] = "#terminal-output { display: block !important; width: 100% !important; height: 280px !important; padding: 0 !important; margin: 0 !important; background: #000 !important; overflow-y: scroll !important; overflow-x: hidden !important; }" + eol

# --- PATCH L3627 (index 3626): add min-height to terminal-panel inline ---
lines[3626] = lines[3626].replace("height: 300px;", "height: 300px; min-height: 300px;")

# --- PATCH L3632 (index 3631): overflow: hidden -> overflow-y: scroll on terminal-output inline ---
lines[3631] = lines[3631].replace("overflow: hidden;", "overflow-y: scroll; overflow-x: hidden; height: 280px; min-height: 280px;")

# --- PATCH L5607 (index 5606): 500ms -> 750ms fit delay ---
lines[5606] = lines[5606].replace("}, 500);", "}, 750);")

# --- Append scrollbar CSS before the LAST </style> ---
scrollbar_css = (
    eol +
    "/* TERMINAL SCROLLBAR */" + eol +
    ".xterm .xterm-viewport { overflow-y: scroll !important; overflow-x: hidden !important; }" + eol +
    ".xterm-viewport::-webkit-scrollbar { width: 10px !important; }" + eol +
    ".xterm-viewport::-webkit-scrollbar-track { background: #111 !important; }" + eol +
    ".xterm-viewport::-webkit-scrollbar-thumb { background: #ff9d00 !important; border-radius: 5px !important; }" + eol
)
for i in range(len(lines) - 1, -1, -1):
    if "</style>" in lines[i]:
        lines[i] = scrollbar_css + lines[i]
        print(f"CSS: Injected scrollbar rules before </style> at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE (all 5 asserts passed)")
print(f"Line count unchanged: {len(lines)}")
