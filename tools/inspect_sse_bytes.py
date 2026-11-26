import json
import urllib.request

url = 'http://127.0.0.1:5000/api/ai/chat'
body = json.dumps({'prompt': "Reply with: It's a student'sAPS"}).encode()
req = urllib.request.Request(url, data=body, method='POST', headers={
    'Content-Type': 'application/json',
})
with urllib.request.urlopen(req, timeout=120) as resp:
    for raw in resp:
        if raw.startswith(b'data: ') and b'[DONE]' not in raw:
            print(repr(raw[:200]))
            break
