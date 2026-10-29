content = open('ACEsi.html', 'r', encoding='utf-8').read()
idx = content.find('<div id="main">')
open('main_snippet.txt', 'w', encoding='utf-8').write(content[idx:idx+8000])
