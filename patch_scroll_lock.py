import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

css = """
/* FORCE XTERM SCROLLBAR TO STAY */
#terminal-output .xterm-viewport {
    overflow-y: scroll !important;
    overflow-x: hidden !important;
    background: #000 !important;
}
#terminal-output .xterm-viewport::-webkit-scrollbar {
    width: 12px !important;
    display: block !important;
}
#terminal-output .xterm-viewport::-webkit-scrollbar-track {
    background: #222 !important;
    border-left: 1px solid #444 !important;
}
#terminal-output .xterm-viewport::-webkit-scrollbar-thumb {
    background: #ff9d00 !important;
    border-radius: 6px !important;
    min-height: 20px !important;
}
"""
for i in range(len(lines) - 1, -1, -1):
    if "</style>" in lines[i]:
        lines[i] = css + eol + lines[i]
        print(f"CSS: Injected scrollbar lock before </style> at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
