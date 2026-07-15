import requests
import re
url = 'https://www.univen.ac.za/students/student-support-services/how-to-apply/'
html = requests.get(url, timeout=20).text
print('gw1startup', 'gw1startup' in html)
print('prodi41', 'prodi41' in html)
print('ITS_OAP', 'ITS_OAP' in html)
print('apply-online', 'apply-online' in html)
print('apply now', 'apply now' in html.lower())
links = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
print('link count', len(links))
for u in links:
    if any(x in u.lower() for x in ['apply-online', 'apply', 'pls/prodi41', 'gw1startup', 'its_oap']):
        print(u)
