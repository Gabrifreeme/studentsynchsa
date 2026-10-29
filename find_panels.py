content = open('ACEsi.html', 'r', encoding='utf-8').read()
for tag in ['chat-panel', 'code-panel', 'explore-panel', '<div id="main"']:
    idx = content.find(tag)
    if idx != -1:
        print(tag, 'at', idx)
        print(content[idx:idx+200])
        print('---')
