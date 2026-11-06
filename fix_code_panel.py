content = open('ACEsi.html', 'r', encoding='utf-8').read()
old = '''    <div id="spinner-wrap" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100px; height: 100px; z-index: 10; display: none;">
      <div id="spinner" style="width: 100%; height: 100%; box-sizing: border-box; border: 8px solid rgba(217, 108, 0, 0.2); border-top: 8px solid #D96C00; border-radius: 50%; animation: spin 1s linear infinite;"></div>
    </div>
    <div id="code-header">
      <div class="toolbar-spacer"></div>
      <div id="code-actions">
        <input id="searchInput" placeholder="Find in file..." title="Search (Ctrl+F)">
        <button class="btn btn-icon" onclick="toggleSearch()" title="Search (Ctrl+F)">⌕</button>
        <button class="btn btn-icon" onclick="clearCode()" title="Clear editor">🗑</button>
        <button class="btn btn-icon" onclick="copyCode()" title="Copy code">⧉</button>
        <button class="btn btn-icon" onclick="saveCode()" title="Save code">💾</button>
      </div>
      <div class="toolbar-spacer"></div>
      <button class="min-btn" onclick="minPanel('code-panel')" title="Minimize panel">-</button>
    </div>
    <div id="code-editor-wrap">
      <div id="line-numbers">1</div>
      <div id="code-editor" contenteditable="true"></div>
    </div>'''
new = '''    <div style="padding: 18px; color: var(--text); font-family: var(--sans);">
      <h2 style="font-size: 16px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #ff9d00; border-bottom: 1px solid #ff9d00; padding-bottom: 10px; margin-bottom: 14px;">Reminders & Deadlines</h2>
      <div style="background: #0a0a0a; border: 1px solid #ff9d00; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
        <strong style="color: #ff9d00; font-size: 13px;">No upcoming deadlines</strong>
        <p style="font-size: 12px; color: rgba(255,157,0,0.7); margin-top: 4px;">Check back once student system sync is active.</p>
      </div>
      <div style="background: #0a0a0a; border: 1px solid #ff9d00; border-radius: 6px; padding: 14px;">
        <strong style="color: #ff9d00; font-size: 13px;">Assignment due</strong>
        <p style="font-size: 12px; color: rgba(255,157,0,0.7); margin-top: 4px;">No submissions pending.</p>
      </div>
    </div>'''
content = content.replace(old, new)
open('ACEsi.html', 'w', encoding='utf-8').write(content)
print('Fixed code-panel')
