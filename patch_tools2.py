with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()
idx = content.find('"cdp_connect": (tool_cdp_connect')
print(repr(content[idx:idx+400]))