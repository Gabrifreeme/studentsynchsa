import re

p = r'C:\Users\gabri\Documents\LibSyncStudent\lib\data\datasources\mock_university_data.dart'
s = open(p, encoding='utf-8', errors='replace').read()
fixes = {
    'uwc': 'https://student.uwc.ac.za/',
    'univen': 'https://www.univen.ac.za/students/student-support-services/how-to-apply/apply-online/',
}
for uid, url in fixes.items():
    pattern = r"(id: '" + uid + r"',.*?applicationUrl: ')([^']*)(')"
    s, n = re.subn(pattern, lambda m: m.group(1) + url + m.group(3),
                   s, count=1, flags=re.S)
    print('dart', uid, n)
open(p, 'w', encoding='utf-8', errors='replace', newline='').write(s)

p2 = r'D:\projects\acesi\tools\generate_offline_guides.py'
s = open(p2, encoding='utf-8').read()
s = s.replace("'uwc': 'https://www.uwc.ac.za/apply',",
              "'uwc': 'https://student.uwc.ac.za/',")
s = s.replace(
    "'univen': 'https://univenerp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP',",
    "'univen': 'https://www.univen.ac.za/students/student-support-services/how-to-apply/apply-online/',")
open(p2, 'w', encoding='utf-8', newline='').write(s)
print('generator updated')
