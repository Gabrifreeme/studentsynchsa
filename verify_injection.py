with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
# Check for memory injection in the system prompt construction
search1 = '_memory_content'
search2 = 'memory.txt'
search3 = 'os.path.exists'
print('Has _memory_content:', search1 in content)
print('Has memory.txt in injection:', search2 in content)
print('Has os.path.exists check:', search3 in content)