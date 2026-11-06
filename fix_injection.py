with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the memory injection in the system prompt construction
# Look for the "Memory note" pattern
idx = content.find('Memory note')
if idx > 0:
    # Show 300 chars around it
    start = max(0, idx - 50)
    end = min(len(content), idx + 300)
    print('Memory note section:')
    print(content[start:end])
else:
    print('Memory note not found')
    # Try alternative
    for pattern in ['_memory_content', 'memory_content', 'Memory .content']:
        idx2 = content.find(pattern)
        if idx2 > 0:
            print(f'Found "{pattern}" at {idx2}')
            end2 = min(len(content), idx2 + 200)
            print(content[idx2:end2])