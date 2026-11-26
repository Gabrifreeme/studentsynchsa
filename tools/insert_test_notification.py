import json
import urllib.request

base = 'https://hqbppkzevmfooyphvhma.supabase.co/rest/v1/app_notifications'
key = 'sb_publishable_5i6tKxRnhdcD6aVhP1PIHQ_3ZJ9t451'
payload = json.dumps({
    'title': 'gmail: Venda University',
    'body': 'You received an email from Venda University about your application.',
    'sender': 'admissions@univen.ac.za',
}).encode('utf-8')
req = urllib.request.Request(base, data=payload, method='POST', headers={
    'apikey': key,
    'Authorization': 'Bearer ' + key,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
})
with urllib.request.urlopen(req, timeout=20) as resp:
    print(resp.status, resp.read().decode())
