content = open('ACEsi.html', 'r', encoding='utf-8').read()

# Replace middle panel (code-panel) inner content
old_code_inner = '''    <div id="spinner-wrap" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100px; height: 100px; z-index: 10; display: none;">
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
      <div id="code-editor" contenteditable="true" spellcheck="false"># Welcome to ACEsi
# Type or paste code, then run with the button above.
# This panel is your live workspace.</div>
    </div>'''

new_reminders = '''    <div style="padding: 18px; color: var(--text); font-family: var(--sans);">
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

content = content.replace(old_code_inner, new_reminders)

# Replace right panel (explore-panel) inner content
old_explore_inner = '''    <div id="explore-header"><span class="panel-label">Explorer</span> <span style="display:flex;align-items:center;gap:6px;"><button class="icon-btn" onclick="loadExplorer()" title="Refresh">⟳</button><button class="min-btn" onclick="minPanel('explore-panel')" title="Minimize panel">-</button></span></div>
    <div id="explorer">Loading...</div>'''

new_bursaries = '''    <div id="explore-header"><span class="panel-label">Bursaries & Announcements</span> <span style="display:flex;align-items:center;gap:6px;"><button class="min-btn" onclick="minPanel('explore-panel')" title="Minimize panel">-</button></span></div>
    <div id="explorer" style="padding: 14px; color: var(--text); font-family: var(--sans); font-size: 13px;">
      <div style="background: #0a0a0a; border: 1px solid #ff9d00; border-radius: 6px; padding: 14px; margin-bottom: 10px;">
        <h3 style="font-size: 14px; font-weight: 700; color: #ff9d00; margin-bottom: 6px;">NSFAS applications open soon</h3>
        <p style="font-size: 12px; color: rgba(255,157,0,0.8);">Prepare your ID and proof of income. Deadlines will be posted here.</p>
      </div>
      <div style="background: #0a0a0a; border: 1px solid #ff9d00; border-radius: 6px; padding: 14px;">
        <h3 style="font-size: 14px; font-weight: 700; color: #ff9d00; margin-bottom: 6px;">Bursary announcements</h3>
        <p style="font-size: 12px; color: rgba(255,157,0,0.8);">Check this panel for new funding opportunities.</p>
      </div>
    </div>'''

content = content.replace(old_explore_inner, new_bursaries)

open('ACEsi.html', 'w', encoding='utf-8').write(content)
print('Updated ACEsi.html')
