with open(r'C:\Users\chris\LipSyncStudent\server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
idx = content.find('@app.route("/api/ping"')
if idx > 0:
    after = content[idx:idx+500]
    print('AFTER (first 500):')
    print(after[:500])
else:
    print('Ping route not found')