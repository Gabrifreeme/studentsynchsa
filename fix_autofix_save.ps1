# fix_autofix_save.ps1
# Fixes the Auto Fix "Save to File" button in ACEsi.html so it prompts for a
# filename when no file is currently selected in the Editor (window.currentFile
# is null/empty). Without this, the backend /api/save-file rejects the request
# with "Missing filename or content" because _ide_path('') returns None.
# Uses Python for safe exact-text editing (no line numbers, no raw \n mangling).
# Run: powershell -ExecutionPolicy Bypass -File fix_autofix_save.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "fix_autofix_save.py"

@'
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\ACEsi.html"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

edits = []

edits.append((r'''        function saveFixedCode() {
            var pane = document.getElementById('autofix-code');
            var fixed = pane ? pane.innerText : (window._autofix.fixed || '');
            if (!fixed) { alert('No fixed code to save.'); return; }
            fetch('http://127.0.0.1:5000/api/save-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: fixed, filename: window.currentFile || '' })
            })''',
r'''        function saveFixedCode() {
            var pane = document.getElementById('autofix-code');
            var fixed = pane ? pane.innerText : (window._autofix.fixed || '');
            if (!fixed) { alert('No fixed code to save.'); return; }
            var filename = window.currentFile || '';
            if (!filename) {
                filename = prompt('Enter filename to save (e.g. lib/main.dart):', '');
                if (!filename) { return; } // user cancelled
            }
            fetch('http://127.0.0.1:5000/api/save-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: fixed, filename: filename })
            })'''))

for i, (old, new) in enumerate(edits, 1):
    count = text.count(old)
    if count == 0:
        print(f"EDIT {i}: FAILED — old text not found")
        print("--- start ---")
        print(old[:300])
        print("--- end ---")
        sys.exit(1)
    elif count > 1:
        print(f"EDIT {i}: FAILED — old text found {count} times (ambiguous)")
        sys.exit(1)
    text = text.replace(old, new, 1)
    print(f"EDIT {i}: OK")

with open(SERVER, "w", encoding="utf-8-sig", newline="") as f:
    f.write(text.replace("\n", "\r\n"))

with open(SERVER, "rb") as f:
    raw = f.read()
print(f"BOM: {raw[:3] == b'\xef\xbb\xbf'}")
print(f"CRLF count: {raw.count(b'\r\n')}")
print(f"bare LF count: {raw.count(b'\n') - raw.count(b'\r\n')}")
print("\nDone — Auto Fix save now prompts for a filename when none is selected.")
'@ | Set-Content -Path $pyScript -Encoding UTF8

python $pyScript

Write-Host "`nDone. Refresh ACEsi in your browser."
