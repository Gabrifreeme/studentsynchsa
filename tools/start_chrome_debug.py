import json
import urllib.request

cmd = 'flutter run -d chrome'
req = urllib.request.Request(
    'http://127.0.0.1:5000/run',
    data=json.dumps({'command': cmd}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=60) as resp:
    print(resp.status, resp.read().decode()[:400])
