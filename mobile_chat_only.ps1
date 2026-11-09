# mobile_chat_only.ps1
# On phones/tablets (<=768px), ACEsi shows only the Conversation (chat) panel.
# The Code Editor and Explorer panels are hidden entirely so nothing is
# cramped or squashed on small screens.
# Uses Python for safe exact-text editing (no line numbers, no raw \n mangling).
# Run: powershell -ExecutionPolicy Bypass -File mobile_chat_only.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "mobile_chat_only.py"

@'
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\ACEsi.html"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

edits = []

edits.append((r'''            #chat-panel,
            #code-panel,
            #explorer-panel {
                width: 100% !important;
                min-height: 200px;
                max-height: none !important;
                overflow: visible !important;
                margin: 3px !important;
            }

            /* Chat panel takes most of the vertical space on phone */
            #chat-panel {
                min-height: 300px;
            }

            /* Code panel smaller on phone */
            #code-panel {
                min-height: 150px;
            }

            /* Explorer panel smaller on phone */
            #explorer-panel {
                min-height: 150px;
            }''',
r'''            /* On phone/tablet: only show the Conversation panel.
               Hide the Code Editor and Explorer entirely so nothing
               is cramped or squashed. */
            #code-panel,
            #explorer-panel {
                display: none !important;
                width: 0 !important;
                height: 0 !important;
                min-height: 0 !important;
                max-height: 0 !important;
                overflow: hidden !important;
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
            }

            /* Chat panel takes full width and most of the screen */
            #chat-panel {
                width: 100% !important;
                min-height: 60vh;
                max-height: none !important;
                overflow: visible !important;
                margin: 3px !important;
                flex: 1 !important;
            }'''))

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
print("\nDone — code and explorer panels hidden on mobile.")
'@ | Set-Content -Path $pyScript -Encoding UTF8

python $pyScript

Write-Host "`nDone. Refresh ACEsi in your browser. On phones/tablets, only the Conversation panel shows."
