with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace smart quotes with regular quotes
content = content.replace('\u201c', '"')
content = content.replace('\u201d', '"')

with open('C:/Users/chris/LipSyncStudent/server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed smart quotes in server.py')