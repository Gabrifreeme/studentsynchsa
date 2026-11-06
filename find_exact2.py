with open(r'C:\Users\chris\StudentSyncSA\server.py', 'rb') as f:
    content = f.read()

# Find the exact tool definition pattern
idx = content.find(b'{"name": "run_command"}')
if idx >= 0:
    print(f'Found at byte index {idx}')
    print(repr(content[idx-50:idx+100]))
else:
    print('Not found with exact pattern')
    
# Also check for the full pattern
idx2 = content.find(b'"name": "run_command"')
if idx2 >= 0:
    print(f'Found with quotes at byte index {idx2}')
else:
    print('Not found with quotes either')