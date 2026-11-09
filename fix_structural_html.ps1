# fix_structural_html.ps1
# Fixes structural HTML issues in ACEsi.html:
# 1. Removes malformed <div id="dev-toolbar"</div> tag (missing >)
# 2. Removes extra </script> tags that break parsing
# 3. Removes duplicate </body> and stray <script> after </body>
# 4. Wraps settings JS block in proper <script>...</script> tags
# Run: powershell -ExecutionPolicy Bypass -File fix_structural_html.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "fix_structural_html.py"

@'
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\ACEsi.html"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

fixes = []

# Fix 1: Remove broken div tag <div id="dev-toolbar"</div>
fixes.append((r'''    <div id="dev-toolbar"</div>

    <div id="dev-toolbar"''', r'''    <div id="dev-toolbar"'''))

# Fix 2: Remove extra </script> tags after jsdiff script
fixes.append((r'''    </script>
    </script>

    <style>''', r'''    </script>

    <style>'''))

# Fix 3: Remove extra </script> tags around runSelected script
fixes.append((r'''    </script>
    </script>
    </script>
    <script>
        function runSelected()''', r'''    </script>
    <script>
        function runSelected()'''))

# Fix 4: Remove extra </script> tags around bottom-status div
fixes.append((r'''    </script>
    </script>
    </script>
    <div id="bottom-status"''', r'''    </script>
    <div id="bottom-status"'''))

# Fix 5: Remove duplicate </body> before stray <script> after </body>
fixes.append((r'''    </script>

</body>
<script>
window.splitVideoPrompt = function() {''', r'''    </script>

<script>
window.splitVideoPrompt = function() {'''))

# Fix 6: Remove any remaining duplicate </body>
fixes.append((r'''};

</script>
</body>
</html>''', r'''};

</script>
</body>
</html>'''))

for i, (old, new) in enumerate(fixes, 1):
    count = text.count(old)
    if count == 0:
        print(f"Fix {i}: WARNING - pattern not found")
    elif count > 1:
        print(f"Fix {i}: WARNING - pattern found {count} times (ambiguous)")
    else:
        text = text.replace(old, new, 1)
        print(f"Fix {i}: OK")

with open(SERVER, "w", encoding="utf-8-sig", newline="") as f:
    f.write(text.replace("\n", "\r\n"))

with open(SERVER, "rb") as f:
    raw = f.read()
print(f"BOM: {raw[:3] == b'\xef\xbb\xbf'}")
print(f"CRLF count: {raw.count(b'\r\n')}")
print(f"bare LF count: {raw.count(b'\n') - raw.count(b'\r\n')}")
print(f"<script> count: {raw.count(b'<script')}")
print(f"</script> count: {raw.count(b'</script>')}")
print(f"<body> count: {raw.count(b'<body>')}")
print(f"</body> count: {raw.count(b'</body>')}")
print(f"<html> count: {raw.count(b'<html>')}")
print(f"</html> count: {raw.count(b'</html>')}")
print(f"Broken dev-toolbar count: {raw.count(b'<div id=dev-toolbar</div>')}")
print("\nDone - structural HTML fixes applied.")
'@ | Set-Content -Path $pyScript -Encoding UTF8

python $pyScript

# Restart server
try {
    Invoke-RestMethod -Uri http://127.0.0.1:5000/restart -Method POST -ContentType 'application/json' -Body '{}' -TimeoutSec 10 | Out-Null
    Write-Host "Server restart requested."
} catch {
    Write-Host "Server restart request failed: $($_.Exception.Message)"
}

Write-Host "`nDone. Refresh ACEsi in your browser."
