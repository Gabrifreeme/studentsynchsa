import re

p = r'C:\Users\gabri\Documents\LibSyncStudent\lib\data\datasources\mock_university_data.dart'
s = open(p, encoding='utf-8', errors='replace').read()
blocks = re.findall(r'University\(\s*(.*?)\s*\),', s, re.S)
print('count', len(blocks))
for b in blocks:
    d = dict(re.findall(r"(\w+):\s*'([^']*)'", b))
    print(d.get('id'), '|', d.get('shortName'), '|', d.get('name'), '|', d.get('province'))
