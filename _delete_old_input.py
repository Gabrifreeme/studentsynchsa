import re

p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
src = open(p, 'r', encoding='utf-8').read()

# Find and remove the old input box AND its wrapping div
# The structure is likely: <div style="..."> <input id="terminal-input" ...> </div>
patterns = [
    # Match a div with "Type a command..." input inside
    re.compile(r'<div[^>]*>\s*<input[^>]*id="terminal-input"[^>]*>\s*</div>', re.DOTALL),
    # Or just the input on its own
    re.compile(r'<input[^>]*id="terminal-input"[^>]*>', re.DOTALL),
]

removed = False
for pattern in patterns:
    match = pattern.search(src)
    if match:
        src = pattern.sub('<!-- Old terminal input removed -->', src, count=1)
        removed = True
        print(f"REMOVED: {match.group(0)[:100]}...")
        break

if not removed:
    print("COULD NOT FIND INPUT - searching differently")
    # Last resort: find the line and remove surrounding div
    lines = src.split('\n')
    for i, line in enumerate(lines):
        if 'terminal-input' in line:
            print(f"Found at line {i+1}: {line[:100]}")
            # Remove this line and the one before if it's a <div>
            if i > 0 and '<div' in lines[i-1]:
                lines[i-1] = ''
            lines[i] = ''
            src = '\n'.join(lines)
            removed = True
            print("LINE REMOVED")
            break

open(p, 'w', encoding='utf-8').write(src)
if removed:
    print("SUCCESS - OLD INPUT REMOVED")
else:
    print("FAILED - MANUAL INSPECTION NEEDED")