with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
idx = content.find('/api/settings", methods=["POST"]')
idx2 = content.find('@app.route', idx+1)
print('End of api_settings_post at:', idx2)
if idx2 > 0:
    between = content[idx:idx2]
    # Find "# ACEsi System Settings" or the next route marker
    for marker in ['# ACEsi', '# =====', '# -----']:
        pos = between.find(marker)
        if pos > 0:
            print(f'Found "{marker}" at position {pos} in between')
            print('Context:')
            print(between[pos-20:pos+100])
            break