with open(r'C:\Users\chris\StudentSyncSA\server.py', 'rb') as f:
    content = f.read()

# Find the curl entry in bytes
idx = content.find(b'{"name": "curl"}')
if idx >= 0:
    print(f'curl at byte index {idx}')
    # Find the next tool after curl
    next_tool = content.find(b'{"name":', idx + 10)
    if next_tool >= 0:
        print(f'Next tool at byte index {next_tool}')
        print(repr(content[idx:next_tool+50]))
    else:
        print('No next tool found')
else:
    print('curl not found')