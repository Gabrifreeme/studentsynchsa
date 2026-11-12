import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# 1. Ensure scrollback is in the Terminal config
for i, line in enumerate(lines):
    if "var term = new Terminal({" in line:
        if "scrollback" not in lines[i+1]:
            lines.insert(i+1, "        scrollback: 2000," + eol)
            print("JS: Ensured scrollback: 2000 is enabled")
        break

# 2. Inject the CSS scrollbar rules before the LAST </style>
css = """
/* NATIVE XTERM SCROLLBAR */
#terminal-output .xterm-viewport {
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    height: 100% !important;
    background: #000 !important;
}
#terminal-output .xterm-viewport::-webkit-scrollbar {
    width: 10px !important;
}
#terminal-output .xterm-viewport::-webkit-scrollbar-track {
    background: #111 !important;
    border-left: 1px solid #333 !important;
}
#terminal-output .xterm-viewport::-webkit-scrollbar-thumb {
    background: #ff9d00 !important;
    border-radius: 5px !important;
}
"""
for i in range(len(lines) - 1, -1, -1):
    if "</style>" in lines[i]:
        lines[i] = css + eol + lines[i]
        print(f"CSS: Injected scrollbar rules before </style> at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"PATCH COMPLETE: {len(lines)} lines")
