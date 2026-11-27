import concurrent.futures, requests

new = {
 'cput': 'https://www.cput.ac.za/study-at-cput/undergraduate/apply',
 'dut': 'https://onlineapps.dut.ac.za/',
 'ru': 'https://ross.ru.ac.za/',
 'spu': 'https://applications-prod.spu.ac.za/',
 'su': 'https://www.su.ac.za/en/apply/undergrad',
 'tut': 'https://applications-prod.tut.ac.za/',
 'uchenn': 'https://applyonline.uct.ac.za/',
 'uj': 'https://www.uj.ac.za/Apply',
 'ukzn': 'https://applications.ukzn.ac.za/',
 'ul': 'https://ulc-prod-webserver.ul.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
 'wsu': 'https://applications.wsu.ac.za/',
 'wits': 'https://www.wits.ac.za/applications/',
 'cut': 'https://www.cut.ac.za/admission-online',
 'zululand': 'https://www.cao.ac.za/',
}

def probe(item):
    k, u = item
    try:
        r = requests.get(u, timeout=15, allow_redirects=True,
                         headers={'User-Agent': 'Mozilla/5.0'})
        return k, r.status_code, r.url
    except Exception as e:
        return k, 'ERR', str(e)[:70]

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for k, status, final in ex.map(probe, new.items()):
        print(f'{k:10} {status} {final}')
