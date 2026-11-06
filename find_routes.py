with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
idx = content.find('/api/settings", methods=["POST"]')
print('Found POST at:', idx)
if idx > 0:
    after = content[idx:idx+500]
    print('After POST (500 chars):')
    print(after[:500])
else:
    print('Not found')