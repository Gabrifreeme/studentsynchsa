with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
# Search for memory-related injection
for pattern in ['memory.txt', '_memory', 'Memory note', '_memory_content']:
    idx2 = content.find(pattern)
    if idx2 > 0:
        print(f'Found "{pattern}" at {idx2}')
        print(content[max(0,idx2-50):idx2+150])
        print('---')