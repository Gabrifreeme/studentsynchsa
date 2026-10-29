with open('main_snippet.txt', 'r', encoding='utf-8') as f:
    content = f.read()
code_idx = content.find('id="code-panel"')
exp_idx = content.find('id="explore-panel"')
with open('panel_extract.txt', 'w', encoding='utf-8') as out:
    out.write('=== code-panel ===\n')
    out.write(content[code_idx-30:code_idx+1200] + '\n')
    out.write('=== explore-panel ===\n')
    out.write(content[exp_idx-30:exp_idx+1200] + '\n')
