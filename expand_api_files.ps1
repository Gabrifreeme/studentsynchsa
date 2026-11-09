# expand_api_files.ps1
# Expands /api/files in server.py to scan the project root (_IDE_ROOT) instead
# of only _IDE_LIB, including .dart/.py/.html/.yaml/.json/.md files and
# skipping heavy folders (.git, build, node_modules, .dart_tool, android, ios,
# windows, linux, macos, web, __pycache__).
# Uses Python for safe exact-text editing (no line numbers, no raw \n mangling).
# Run: powershell -ExecutionPolicy Bypass -File expand_api_files.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "expand_api_files.py"

@'
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\server.py"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

edits = []

edits.append((r'''@app.route('/api/files', methods=['GET'])
def api_files():
    files = []
    if os.path.isdir(_IDE_LIB):
        for root, _dirs, names in os.walk(_IDE_LIB):
            for name in names:
                if name.endswith('.dart'):
                    rel = os.path.relpath(os.path.join(root, name), _IDE_ROOT)
                    files.append(rel.replace('\\', '/'))
    return jsonify(sorted(files))''',
r'''@app.route('/api/files', methods=['GET'])
def api_files():
    files = []
    _IDE_EXCLUDE_DIRS = {
        '.git', 'build', 'node_modules', '.dart_tool',
        'android', 'ios', 'windows', 'linux', 'macos', 'web',
        '__pycache__',
    }
    _IDE_EXTENSIONS = {'.dart', '.py', '.html', '.yaml', '.json', '.md'}
    if os.path.isdir(_IDE_ROOT):
        for root, dirs, names in os.walk(_IDE_ROOT):
            # Skip heavy/excluded directories in-place so os.walk doesn't descend
            dirs[:] = [d for d in dirs if d not in _IDE_EXCLUDE_DIRS]
            for name in names:
                ext = os.path.splitext(name)[1].lower()
                if ext in _IDE_EXTENSIONS:
                    rel = os.path.relpath(os.path.join(root, name), _IDE_ROOT)
                    files.append(rel.replace('\\', '/'))
    return jsonify(sorted(files))'''))

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

import py_compile
try:
    py_compile.compile(SERVER, doraise=True)
    print("Compile check: COMPILES OK")
except py_compile.PyCompileError as e:
    print(f"Compile check: FAILED — {e}")
    sys.exit(1)

print("\nDone — /api/files now scans project root with broader extensions and excluded folders.")
'@ | Set-Content -Path $pyScript -Encoding UTF8

# Run the Python edit script
python $pyScript

# Restart the server so the change goes live
try {
    Invoke-RestMethod -Uri http://127.0.0.1:5000/restart -Method POST -ContentType 'application/json' -Body '{}' -TimeoutSec 10 | Out-Null
    Write-Host "Server restart requested."
} catch {
    Write-Host "Server restart request failed: $($_.Exception.Message)"
}

Write-Host "`nDone. Refresh ACEsi in your browser — the Explorer will now show the full project tree."
