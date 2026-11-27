import re

p = r'C:\Users\gabri\Documents\LibSyncStudent\lib\data\datasources\mock_university_data.dart'
s = open(p, encoding='utf-8', errors='replace').read()

apply_fixes = {
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
    'wits': 'https://www.wits.ac.za/undergraduate/apply-to-wits/',
    'cut': 'https://www.cut.ac.za/admission-online',
    'zululand': 'https://www.cao.ac.za/',
}
website_fixes = {
    'su': 'https://www.su.ac.za',
}

for uid, url in apply_fixes.items():
    pattern = r"(id: '" + uid + r"',.*?applicationUrl: ')([^']*)(')"
    s, n = re.subn(pattern, lambda m: m.group(1) + url + m.group(3), s,
                   count=1, flags=re.S)
    print('apply', uid, n)
for uid, url in website_fixes.items():
    pattern = r"(id: '" + uid + r"',.*?website: ')([^']*)(')"
    s, n = re.subn(pattern, lambda m: m.group(1) + url + m.group(3), s,
                   count=1, flags=re.S)
    print('website', uid, n)

open(p, 'w', encoding='utf-8', errors='replace', newline='').write(s)
print('done')
