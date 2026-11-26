import json
import urllib.request

base_loop = 'http://127.0.0.1:5000'
base_lan = 'http://192.168.0.117:5000'

req = urllib.request.Request(
    base_loop + '/api/auth/issue',
    data=json.dumps({'display_name': 'loopback'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=20) as resp:
    auth = json.loads(resp.read())
token = auth.get('token') or auth.get('access_token')
print('token issued:', bool(token))

req = urllib.request.Request(
    base_lan + '/email/check?force=1',
    headers={'X-ACEsi-Token': token},
)
with urllib.request.urlopen(req, timeout=120) as resp:
    print(resp.status, resp.read().decode())
