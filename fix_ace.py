with open('ACEsi.html','r',encoding='utf-8') as f:
    content = f.read()

modal = '''<div id="autofix-modal-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:800;align-items:center;justify-content:center;flex-direction:column;"><div id="autofix-modal" style="width:720px;max-width:92vw;height:80vh;background:#000000;border:2px solid #ff9d00;border-radius:12px;display:flex;flex-direction:column;box-shadow:0 0 30px rgba(255,157,0,0.3);margin:20px;"><div style="display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:2px solid #ff9d00;background:#0a0a0a;border-radius:10px 10px 0 0;flex-shrink:0;"><h2 style="margin:0;font-size:16px;font-weight:700;color:#ff9d00;letter-spacing:1px;">Auto-Fix Code</h2><button onclick="document.getElementById('autofix-modal-overlay').style.display='none'" title="Close" style="background:transparent;border:1px solid #ff9d00;color:#ff9d00;border-radius:6px;padding:6px 14px;font-size:13px;cursor:pointer;font-family:inherit;">Close ✕</button></div><div style="padding:14px 20px;flex-shrink:0;background:#000000;border-bottom:1px solid #ff9d00;"><label style="color:#ff9d00;font-size:13px;font-weight:600;display:block;margin-bottom:6px;">Paste your broken code here:</label></div><textarea id="autofix-input" rows="12" placeholder="Paste broken Dart/JS/HTML code here..." spellcheck="false" style="flex:1;background:#000000;color:#ff9d00;font-family:var(--mono);font-size:13.5px;line-height:1.65;padding:16px 20px;border:none;resize:none;outline:none;white-space:pre-wrap;word-wrap:break-word;word-break:break-word;overflow:auto;border-radius:0 0 10px 10px;"></textarea><div style="display:flex;gap:12px;padding:14px 20px;border-top:2px solid #ff9d00;background:#0a0a0a;border-radius:0 0 10px 10px;flex-shrink:0;align-items:center;justify-content:space-between;"><button onclick="document.getElementById('autofix-modal-overlay').style.display='none'" title="Close" style="border:1px solid #ff9d00;background:#000000;color:#ff9d00;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:700;">Close</button><button id="autoFixBtn" title="Send to AI" style="border:1px solid #ff9d00;background:#ff9d00;color:#000;padding:10px 28px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:800;">Fix Code</button><button onclick="autoFixModalCopy()" title="Copy result" style="border:1px solid #ff9d00;background:#000000;color:#ff9d00;padding:8px 20px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:700;">Copy</button></div></div></div>'''

script = '''<script>
function showToast(msg, type) {
  let t = document.getElementById('autofix-toast');
  if (!t) { t = document.createElement('div'); t.id = 'autofix-toast'; t.style.cssText = 'position:fixed;left:50%;bottom:24px;transform:translateX(-50%);max-width:90vw;padding:10px 16px;border-radius:8px;z-index:99999;font:14px sans-serif;color:#fff;box-shadow:0 2px 10px rgba(0,0,0,.4);'; document.body.appendChild(t); }
  t.style.background = (type === 'error') ? '#c62828' : '#2e7d32'; t.textContent = msg; t.style.display = 'block'; clearTimeout(t._timer); t._timer = setTimeout(function() { t.style.display = 'none'; }, (type === 'error') ? 6000 : 2500);
}
function openAutoFixModal() { var m = document.getElementById('autofix-modal-overlay'); if (m) m.style.display = 'flex'; }
function autoFixModalCopy() { var input = document.getElementById('autofix-input'); if (!input) return; if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(input.value || '').then(() => alert('Copied')).catch(() => alert('Copy failed')); } else { input.select(); document.execCommand('copy'); alert('Copied'); } }
let isFixing = false;
async function handleAutoFix() {
  console.log('Button clicked');
  if (isFixing) return;
  const editor = document.getElementById('autofix-input');
  if (!editor) { showToast('Auto-fix: modal input not found', 'error'); return; }
  const code = editor.value || '';
  if (!code.trim()) { showToast('Editor empty — paste broken code first', 'error'); return; }
  isFixing = true;
  const btn = document.getElementById('autoFixBtn');
  if (btn) btn.disabled = true;
  try {
    const response = await fetch('http://127.0.0.1:5000/api/autofix', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) });
    if (!response.ok) throw new Error('Server error (' + response.status + ')');
    const data = await response.json();
    const activeEditor = document.querySelector('.modal textarea, .modal [contenteditable="true"], .modal input[type="text"]');
    if (activeEditor) {
      if (activeEditor.tagName === 'TEXTAREA' || activeEditor.tagName === 'INPUT') activeEditor.value = data.fixed_code;
      else activeEditor.innerText = data.fixed_code;
      showToast('Code fixed!', 'success');
    } else {
      showToast('Error: Could not find editor', 'error');
    }
  } catch (err) { showToast('Auto-Fix failed: ' + (err.message || err), 'error'); }
  finally { isFixing = false; if (btn) btn.disabled = false; }
}
document.getElementById('autoFixBtn').addEventListener('click', handleAutoFix);
</script>'''

content = content.replace('</body>', modal + '\n</body>')
content = content.replace('</html>', script + '\n</html>')
with open('ACEsi.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('restored clean')
