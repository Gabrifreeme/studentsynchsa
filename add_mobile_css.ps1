# add_mobile_css.ps1
# Adds mobile-responsive CSS to ACEsi.html so the three side-by-side panels
# (chat, code, explorer) stack vertically on phones/tablets.
# Uses Python for safe exact-text editing (no line numbers, no raw \n mangling).
# Run: powershell -ExecutionPolicy Bypass -File add_mobile_css.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "add_mobile_css.py"

@'
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\ACEsi.html"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

edits = []

edits.append((r'''</head>''',
r'''    <style>
        /* ===== Mobile responsiveness ===== */
        @media (max-width: 768px) {
            /* Stack the three panels vertically instead of side-by-side */
            #main-container {
                flex-direction: column !important;
                height: auto !important;
                overflow: visible !important;
            }

            #chat-panel,
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
            }

            /* Editor textarea needs room on narrow screens */
            #code-editor {
                font-size: 14px !important;
                line-height: 21px !important;
            }

            #line-numbers {
                font-size: 14px !important;
                line-height: 21px !important;
            }

            /* Chat input: full width, taller for touch */
            #chat-input {
                min-height: 56px !important;
                max-height: 300px !important;
                font-size: 16px !important; /* prevents iOS zoom on focus */
                padding: 10px !important;
            }

            /* Send button: touch-friendly size */
            button[onclick="sendMessage()"] {
                min-height: 56px !important;
                min-width: 70px !important;
                font-size: 16px !important;
                padding: 12px 16px !important;
            }

            /* Mic/speaker/upload button row */
            #chat-input + button,
            button[title="Mic"],
            button[title="Speaker"],
            button[title="Upload"] {
                min-height: 56px !important;
                min-width: 56px !important;
                font-size: 18px !important;
                padding: 10px !important;
            }

            /* Make all buttons touch-friendly */
            button {
                min-height: 44px !important;
                font-size: 14px !important;
            }

            /* Prevent horizontal overflow on narrow screens */
            body {
                overflow-x: hidden !important;
            }

            .panel {
                margin: 3px !important;
            }

            .panel-header {
                padding: 8px !important;
                font-size: 14px !important;
            }

            /* Chat messages panel scrolls, not the whole page */
            #chat-messages {
                padding: 6px !important;
            }

            /* Terminal / dev toolbar area compact */
            #dev-toolbar {
                font-size: 12px !important;
                padding: 4px !important;
                gap: 4px !important;
            }
        }

        /* Small tablets: give panels a bit more room but still stack below ~600px */
        @media (max-width: 600px) and (min-width: 480px) {
            #chat-panel { min-height: 250px; }
            #code-panel { min-height: 120px; }
            #explorer-panel { min-height: 120px; }
        }

        /* Very small phones: panels even tighter */
        @media (max-width: 479px) {
            #chat-panel { min-height: 200px; }
            #code-panel { min-height: 100px; }
            #explorer-panel { min-height: 100px; }
            #code-editor { font-size: 13px !important; line-height: 20px !important; }
            #line-numbers { font-size: 13px !important; line-height: 20px !important; }
        }
    </style>
</head>'''))

for i, (old, new) in enumerate(edits, 1):
    count = text.count(old)
    if count == 0:
        print(f"EDIT {i}: FAILED — old text not found")
        print("--- start ---")
        print(old[:200])
        print("--- end ---")
        sys.exit(1)
    elif count > 1:
        print(f"EDIT {i}: FAILED — old text found {count} times (ambiguous)")
        sys.exit(1)
    text = text.replace(old, new, 1)
    print(f"EDIT {i}: OK")

with open(SERVER, "w", encoding="utf-8-sig", newline="") as f:
    f.write(text.replace("\n", "\r\n"))

print("\nDone — responsive CSS inserted before </head>")
'@ | Set-Content -Path $pyScript -Encoding UTF8

# Run the Python edit script
python $pyScript

Write-Host "`nDone. Refresh ACEsi in your browser to see the mobile layout."
