import re

url = ('https://myadmin.unisa.ac.za/tool/'
       'e7dac559-0533-4ed7-b1aa-2f289a965352/default.do')

p = r'C:\Users\gabri\Documents\LibSyncStudent\lib\data\datasources\mock_university_data.dart'
s = open(p, encoding='utf-8', errors='replace').read()
s, n = re.subn(
    r"(id: 'unisa',.*?applicationUrl: ')([^']*)(')",
    lambda m: m.group(1) + url + m.group(3), s, count=1, flags=re.S)
print('dart', n)
open(p, 'w', encoding='utf-8', errors='replace', newline='').write(s)

p2 = r'D:\projects\acesi\tools\generate_offline_guides.py'
s = open(p2, encoding='utf-8').read()
s = re.sub(r"'unisa': '[^']*',", "'unisa': '" + url + "',", s, count=1)
open(p2, 'w', encoding='utf-8', newline='').write(s)
print('generator updated')
