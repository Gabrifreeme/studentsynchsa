with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Search for the exact tool definition pattern
idx = content.find('{"name": "run_command"')
if idx >= 0:
    print(f'Found at char index {idx}')
    print(repr(content[idx-50:idx+100]))
else:
    print('Not found with exact pattern')
    
# Also check for the full pattern
idx2 = content.find('"name": "run_command"')
if idx2 >= 0:
    print(f'Found with quotes at char index {idx2}')
else:
    print('Not found with quotes either')