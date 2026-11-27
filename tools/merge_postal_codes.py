import io
import re
import urllib.request
import zipfile

DART = r'C:\Users\gabri\Documents\LibSyncStudent\lib\presentation\screens\profile\profile_onboarding_screen.dart'
URL = 'https://download.geonames.org/export/zip/ZA.zip'

PROV = {
    'GP': 'Gauteng',
    'WC': 'Western Cape',
    'KZN': 'KwaZulu-Natal',
    'EC': 'Eastern Cape',
    'FS': 'Free State',
    'LP': 'Limpopo',
    'MP': 'Mpumalanga',
    'NC': 'Northern Cape',
    'NW': 'North West',
}

with urllib.request.urlopen(URL, timeout=120) as resp:
    data = resp.read()
with zipfile.ZipFile(io.BytesIO(data)) as z:
    text = z.read('ZA.txt').decode('utf-8', 'replace')

incoming = {}
for line in text.splitlines():
    parts = line.split('\t')
    if len(parts) < 6:
        continue
    code = parts[1].strip()
    place = parts[2].strip()
    admin1 = parts[4].strip()
    if not re.fullmatch(r'\d{4}', code) or not place:
        continue
    province = PROV.get(admin1, '')
    entry = f'{code} - {place}' + (f', {province}' if province else '')
    incoming.setdefault(code, entry)

s = open(DART, encoding='utf-8', errors='replace').read()
start = s.index('  static const _postalCodes = [')
end = s.index('\n  ];', start)
block = s[start:end]
existing = set(re.findall(r"'(\d{4}) - ", block))
print('existing', len(existing), 'incoming', len(incoming))

missing = [(code, entry) for code, entry in incoming.items() if code not in existing]
missing.sort()
print('adding', len(missing))
lines = [f"    '{entry.replace(chr(39), chr(92) + chr(39))}'," for _, entry in missing]
new_block = block + '\n' + '\n'.join(lines)
s = s[:start] + new_block + s[end:]
open(DART, 'w', encoding='utf-8', errors='replace', newline='').write(s)
print('merged')
