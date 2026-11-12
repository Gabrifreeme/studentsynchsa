import re

p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# 1. Hide the old input box (the one at the bottom of the terminal panel)
# The input has id="terminal-input" and is inside a div with the "Type a command..." placeholder
old_input_wrapper = '''  <div style="display: flex; padding: 4px; background: #111; border-top: 1px solid #333;">
    <input type="text" id="terminal-input" placeholder="Type a command..." style="flex: 1; padding: 8px; background: #111; color: #ff9d00; border: none; outline: none; font-family: monospace; font-size: 12px;">
  </div>'''

if old_input_wrapper in src:
    src = src.replace(old_input_wrapper, '  <!-- Old input box removed - xterm.js handles all input -->')

# 2. Make terminal-output fill the panel properly
src = src.replace(
    '<div id="terminal-output" style="flex: 1 1 auto; min-width: 0; min-height: 0; overflow: hidden; padding: 0; margin: 0; background: #000; display: block; width: 100%;"></div>',
    '<div id="terminal-output" style="flex: 1 1 auto; min-width: 0; min-height: 0; overflow: hidden; padding: 0; margin: 0; background: #000; display: block; width: 100%; height: 100%; position: relative;"></div>'
)

# 3. Remove the old DOMContentLoaded listener that grabs terminal-input (line 5143 area)
# We'll comment out the whole block by finding the pattern
old_listener_pattern = re.compile(
    r"document\.addEventListener\('DOMContentLoaded',\s*function\(\)\s*\{\s*setTimeout\(function\(\)\s*\{\s*var termInput = document\.getElementById\('terminal-input'\);.*?\},\s*\d+\);\s*\}\);",
    re.DOTALL
)
src = old_listener_pattern.sub('// Old terminal listener removed - xterm.js handles everything', src)

open(p, 'w', encoding='utf-8').write(src)
print("OLD TERMINAL SYSTEM KILLED - PURE XTERM MODE")