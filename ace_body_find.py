import re
content = open('ACEsi.html', 'r', encoding='utf-8').read()
for panel in ['chat-panel', 'code-panel', 'explore-panel']:
    idx = content.find(f'id="{panel}"')
    # find the closing tag for this panel - print 1500 chars after open
    with open('ace_panels_out.txt', 'a', encoding='utf-8') as f:
        f.write(f'=== {panel} @ char {idx} ===\n')
        f.write(content[idx:idx+2500])
        f.write('\n')
    print('wrote', panel)
