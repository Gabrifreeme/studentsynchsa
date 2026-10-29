with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

routes = [
    '/api/settings',
    '/api/settings (POST)',
    '/api/reminders',
    '/api/notifications',
    '/api/ping',
    '/api/memory',
    '/api/live_logs',
    '/api/live_logs/clear',
    '/chat',
]

for route in routes:
    # Check various ways the route might appear
    found = route in content
    print(f'{route}: {found}')

print()
print('Total routes checked:', len(routes))