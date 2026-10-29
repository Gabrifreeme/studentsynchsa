with open(r'C:\Users\chris\StudentSyncSA\server.py', 'rb') as f:
    content = f.read()

idx = content.find(b'"name": "run_command"')
if idx >= 0:
    print(f'Found at byte index {idx}')
    print(repr(content[idx-200:idx+200]))
else:
    print('Not found')