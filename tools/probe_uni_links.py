import json, concurrent.futures
import requests

links = json.load(open(r'D:\projects\acesi\tools\uni_links.json', encoding='utf-8'))
urls = []
for u in links:
    urls.append((u['short'], 'site', u['website']))
    urls.append((u['short'], 'apply', u['apply']))

def probe(item):
    short, kind, url = item
    try:
        r = requests.get(url, timeout=12, allow_redirects=True,
                         headers={'User-Agent': 'Mozilla/5.0'})
        return short, kind, url, r.status_code, r.url
    except Exception as e:
        return short, kind, url, 'ERR', str(e)[:90]

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(probe, urls))

for short, kind, url, status, final in results:
    flag = '' if status == 200 else '  <-- CHECK'
    print(f'{short:9} {kind:5} {status} {url}{flag}')
    if status != 200 and kind == 'apply':
        print(f'{"":15}->{final}')
