p = r'C:\Users\chris\LipSyncStudent\ACEsi.html'
lines = open(p, 'r', encoding='utf-8').read().splitlines()

removed = False
for i in range(len(lines) - 2):
    # Look for a stray }); right before </script>
    if lines[i].strip() == '});' and lines[i+1].strip() == '</script>':
        # Confirm the previous line closes the resize handler (ends with });)
        if i > 0 and 'catch(e)' in lines[i-1] or (i > 1 and '}' in lines[i-1]):
            lines[i] = '// orphan removed'
            removed = True
            print(f"REMOVED ORPHAN at line {i+1}")
            break

if not removed:
    # Simpler fallback: find "});" followed by "</script>" anywhere
    for i in range(len(lines) - 1):
        if lines[i].strip() == '});' and lines[i+1].strip() == '</script>':
            lines[i] = '// orphan removed'
            removed = True
            print(f"REMOVED ORPHAN (fallback) at line {i+1}")
            break

if removed:
    open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    print("DONE")
else:
    print("COULD NOT FIND ORPHAN - paste next 5 lines after </script> for diagnosis")