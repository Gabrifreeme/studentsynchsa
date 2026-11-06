with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
# Find the system_prompt construction in the /chat route
idx = content.find('system_prompt = (')
if idx > 0:
    # Show 150 chars after
    after = content[idx:idx+200]
    print('system_prompt construction found')
    print(after[:200])