content = open('ACEsi.html', 'r', encoding='utf-8').read()
idx = content.find('id="code-panel"')
with open('check_code_panel.txt', 'w', encoding='utf-8') as f:
    f.write('Found at ' + str(idx) + '\n')
    f.write(content[idx:idx+2000] + '\n')
