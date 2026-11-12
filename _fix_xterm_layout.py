p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Fix the xterm terminal alignment by forcing the parent and container to have zero padding/margin
# and setting the canvas to start at top-left

css_fix = """
#terminal-panel { box-sizing: border-box !important; padding: 0 !important; margin: 0 !important; }
#terminal-output { box-sizing: border-box !important; padding: 0 !important; margin: 0 !important; display: block !important; position: relative !important; overflow: hidden !important; }
#terminal-output .xterm { padding: 4px !important; margin: 0 !important; }
#terminal-output .xterm-screen { margin: 0 !important; padding: 0 !important; position: absolute !important; top: 0 !important; left: 0 !important; }
#terminal-output .xterm-viewport { overflow-y: auto !important; }
"""

if '#terminal-output .xterm-screen { margin: 0 !important' not in src:
    src = src.replace('</style>', css_fix + '\n</style>', 1)
    open(p, 'w', encoding='utf-8').write(src)
    print("XTERM LAYOUT FIXED")
else:
    print("ALREADY FIXED")