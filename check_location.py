with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
idx = 713750
# Show 300 chars after the POST handler end
after = content[idx:idx+300]
print('After 713750 (300 chars):')
print(after[:300])