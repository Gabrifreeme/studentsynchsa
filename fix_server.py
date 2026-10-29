with open(r'C:\Users\chris\LipSyncStudent\server.py', 'rb') as f:
    content = f.read()
content = content.replace(b'ECHO is on.\n', b'')
with open(r'C:\Users\chris\LipSyncStudent\server.py', 'wb') as f:
    f.write(content)
print("Removed 'ECHO is on.' line")