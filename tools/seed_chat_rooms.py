import json
import urllib.request

base = 'https://hqbppkzevmfooyphvhma.supabase.co/rest/v1/app_messages'
headers = {
    'apikey': 'sb_publishable_5i6tKxRnhdcD6aVhP1PIHQ_3ZJ9t451',
    'Authorization': 'Bearer sb_publishable_5i6tKxRnhdcD6aVhP1PIHQ_3ZJ9t451',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal',
}
for room, text in (
    ('province', 'TEST - Province Base Chat is working'),
    ('university', 'TEST - University Chat is working'),
):
    payload = json.dumps({
        'text': text,
        'user_name': 'Test',
        'user_id': 'wiring-test',
        'room': room,
    }).encode('utf-8')
    req = urllib.request.Request(base, data=payload, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=20) as resp:
        print(room, 'insert', resp.status)
    check = urllib.request.Request(
        base + '?select=id,text&room=eq.' + room,
        headers=headers,
    )
    with urllib.request.urlopen(check, timeout=20) as resp:
        rows = json.loads(resp.read())
        print(room, 'read-back', len(rows), rows[-1]['text'])
