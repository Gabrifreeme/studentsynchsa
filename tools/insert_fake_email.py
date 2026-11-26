import json
import urllib.request

base = 'https://hqbppkzevmfooyphvhma.supabase.co/rest/v1/app_notifications'
key = 'sb_publishable_5i6tKxRnhdcD6aVhP1PIHQ_3ZJ9t451'
payload = json.dumps({
    'title': 'NSFAS',
    'body': 'NSFAS sent you a request to confirm your bank details.',
    'sender': 'no-reply@nsfas.org.za',
}).encode('utf-8')
req = urllib.request.Request(base, data=payload, method='POST', headers={
    'apikey': key,
    'Authorization': 'Bearer ' + key,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal',
})
with urllib.request.urlopen(req, timeout=20) as resp:
    print('insert', resp.status)

check = urllib.request.Request(
    base + '?select=id,title,body&order=created_at.desc&limit=5', headers={
        'apikey': key,
        'Authorization': 'Bearer ' + key,
    })
with urllib.request.urlopen(check, timeout=20) as resp:
    print(json.loads(resp.read()))
