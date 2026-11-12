import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# --- 1. Delete the JS Alignment Lock setTimeout block ---
start_idx = None
for i, line in enumerate(lines):
    if "// JS Alignment Lock injected here:" in line:
        start_idx = i
        break

if start_idx is not None:
    end_idx = start_idx
    while end_idx < len(lines) and "termContainer.style.textAlign = 'left';" not in lines[end_idx]:
        end_idx += 1
    # Delete from start_idx to end_idx (inclusive)
    del lines[start_idx:end_idx + 1]
    print(f"DELETED: JS Alignment Lock hack at lines {start_idx+1}-{end_idx+1}")
else:
    print("WARNING: Could not find JS Alignment Lock hack")

# --- 2. Inject Arena's CSS override ---
css = """
/* ARENA FIX: xterm.js 5.3.0 phantom offset kill switch */
#terminal-panel {
  display: block !important;
  text-align: left !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
  align-content: flex-start !important;
}

#terminal-panel .xterm,
#terminal-panel .xterm-screen,
#terminal-panel .xterm-rows,
#terminal-panel .xterm-rows > div,
#terminal-panel .xterm-rows span {
  margin-left: 0 !important;
  margin-right: 0 !important;
  padding-left: 0 !important;
  text-align: left !important;
  text-indent: 0 !important;
  letter-spacing: normal !important;
  word-spacing: normal !important;
  direction: ltr !important;
  transform: none !important;
}

#terminal-panel .xterm { position: relative !important; }
#terminal-panel .xterm-screen { position: relative !important; left: 0 !important; top: 0 !important; }
#terminal-panel .xterm-viewport { position: absolute !important; left: 0 !important; top: 0 !important; right: 0 !important; }
"""

# Append before the last </style>
for i in range(len(lines) - 1, -1, -1):
    if "</style>" in lines[i]:
        lines[i] = css + eol + lines[i]
        print(f"CSS: Injected Arena's override before </style> at line {i+1}")
        break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print(f"PATCH COMPLETE: {len(lines)} lines")
