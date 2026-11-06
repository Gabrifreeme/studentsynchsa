with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
# Check for memory routes
search1 = '/api/memory"'
search2 = '\"memory\"'
search3 = 'memory.txt'
print('Has /api/memory GET route:', search1 in content)
print('Has memory key in POST:', search2 in content)
print('Has memory.txt reference:', search3 in content)