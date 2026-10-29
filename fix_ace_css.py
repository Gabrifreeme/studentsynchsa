with open('C:\\Users\\chris\\LipSyncStudent\\ACEsi.html','r',encoding='utf-8',errors='ignore') as f:
    lines = f.read().splitlines()
start = None
for i, line in enumerate(lines):
    if '.ace-monokai' in line:
        start = i
        break
if start is not None:
    end = start
    for i in range(start, len(lines)):
        if '.ace-monokai' not in lines[i] and i > start:
            end = i - 1
            break
        end = i
    new_block = [
        '    .ace_editor, .ace_scroller, .ace_content, .ace_layer, .ace_text-layer, .ace_gutter, .ace_gutter-layer { background-color: #000000 !important; color: #ff9d00 !important; }',
        '    .ace_gutter { border-right: 1px solid #ff9d00 !important; }',
        '    .ace_gutter-cell { color: #ff9d00 !important; }',
        '    .ace_cursor { border-left: 2px solid #ff9d00 !important; }',
        '    .ace_selected-word { background: rgba(255,157,0,0.15) !important; }',
        '    .ace_active-line { background: #111111 !important; }',
    ]
    lines[start:end+1] = new_block
    with open('C:\\Users\\chris\\LipSyncStudent\\ACEsi.html','w',encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('replaced lines', start, 'to', end)
