import json
import urllib.request

req = urllib.request.Request(
    'https://integrate.api.nvidia.com/v1/models',
    headers={'Authorization': 'Bearer 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'},
)
with urllib.request.urlopen(req, timeout=40) as resp:
    data = json.loads(resp.read())
ids = [m.get('id') for m in data.get('data', [])]
print('count', len(ids))
for i in ids[:40]:
    print(i)
