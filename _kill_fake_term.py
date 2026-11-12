import re

p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# 1. Remove the old runTerminalCommand function entirely
# It starts with "async function runTerminalCommand()" and ends before the next "function"
pattern = re.compile(r'async function runTerminalCommand\(\)\s*\{.*?\n\s*\}', re.DOTALL)
src, count1 = pattern.subn('// Old fake terminal command removed', src)

# 2. Find and remove the DOMContentLoaded listener that attaches to the old input box
# It might look like: document.getElementById('terminal-input').addEventListener('keydown', ...)
pattern2 = re.compile(r'document\.getElementById\(\s*[\'"]terminal-input[\'"]\s*\)\.addEventListener\([^;]+;', re.DOTALL)
src, count2 = pattern2.subn('// Old terminal input listener removed', src)

# 3. Find and disable the button that opens the terminal if it calls the old function
# The old button might use onclick="showTerminal()" or similar. We will leave the new showTerminalPanel()
# but if it calls the old API, we want to kill that.

open(p, 'w', encoding='utf-8').write(src)
print(f"REMOVED OLD FUNCTIONS: {count1} runTerminalCommand, {count2} input listeners")