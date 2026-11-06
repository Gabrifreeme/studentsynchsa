with open(r'C:\Users\chris\LipSyncStudent\ACEsi.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the Google Drive button location and insert Memory tab after it
marker = 'button onclick="connectGoogleDrive()"'
idx = content.find(marker)
if idx > 0:
    # Insert Memory tab after the Google Drive button's closing tag
    insert_pos = content.find('</button>', idx) + len('</button>')
    insert_pos = content.find('</div>', insert_pos) + len('</div>')
    
    new_tab = '''
        <!-- Memory Tab -->
        <div id="settings-tab-memory" style="display:none; margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid #ff9d00;">
            <div style="font-size:12px;color:#ff9d00;margin-bottom:6px;">Memory</div>
            <textarea id="settings-memory" style="width:100%;height:150px;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:8px;font-family:'Roboto Mono',monospace;font-size:11px;resize:vertical;outline:none;" placeholder="Type memory notes..."></textarea>
            <div style="margin-top:8px; text-align:center;">
                <button onclick="saveMemory()" style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 12px;font-size:11px;">Save Memory</button>
            </div>
        </div>'''
    
    content = content[:insert_pos] + new_tab + content[insert_pos:]
    
    with open(r'C:\Users\chris\LipSyncStudent\ACEsi.html', 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    print('Memory tab added successfully')
else:
    print('Could not find marker location')
PYEOF