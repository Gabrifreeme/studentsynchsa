# add_diff_line_numbers.ps1
# Adds line numbers to BOTH the left (Original) and right (ACESi's Fix) panes
# in the Auto Fix diff modal in ACEsi.html.
# Also fixes saveFixedCode() so saved files exclude line numbers.
# Uses Python for safe exact-text editing (no line numbers, no raw \n mangling).
# Run: powershell -ExecutionPolicy Bypass -File add_diff_line_numbers.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "add_diff_line_numbers.py"

@'
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\ACEsi.html"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

edits = []

# ---------------------------------------------------------------------------
# Edit 1: Add CSS for line-numbered diff rows (after .autofix-pane .ln-ctx)
# ---------------------------------------------------------------------------
edits.append((r'''        .autofix-pane .ln-ctx {
            color: #888;
        }

        #autofix-summary {''',
r'''        .autofix-pane .ln-ctx {
            color: #888;
        }

        /* Line numbers for Auto Fix diff panes */
        .autofix-row {
            display: flex;
            align-items: flex-start;
            min-height: 1.4em;
        }

        .autofix-ln {
            flex-shrink: 0;
            width: 36px;
            text-align: right;
            color: #666;
            user-select: none;
            -webkit-user-select: none;
            padding: 0 8px 0 4px;
            font-family: 'Roboto Mono', monospace;
            font-size: 13px;
            line-height: 1.4em;
        }

        .autofix-code {
            flex: 1;
            min-width: 0;
            padding-left: 4px;
            border-left: 3px solid transparent;
        }

        #autofix-summary {'''))

# ---------------------------------------------------------------------------
# Edit 2: Replace _afixRender() with line-number-aware version + add helper
# ---------------------------------------------------------------------------
edits.append((r'''        function _afixRender() {
            var DiffLib = window.Diff || window.jsdiff;
            if (!DiffLib || !DiffLib.diffLines) {
                document.getElementById('autofix-original').innerText = window._autofix.original || '';
                document.getElementById('autofix-code').innerText = window._autofix.fixed || '';
                return;
            }
            var leftEl = document.getElementById('autofix-original');
            var rightEl = document.getElementById('autofix-code');
            if (!leftEl || !rightEl) return;
            var orig = window._autofix.original || '';
            var fixed = window._autofix.fixed || '';
            if (typeof Diff === 'undefined' || !Diff.diffLines) {
                leftEl.innerHTML = '<span class="ln ln-ctx">' + _afixEscape(orig) + '</span>';
                rightEl.innerHTML = '<span class="ln ln-add">' + _afixEscape(fixed) + '</span>';
                return;
            }
            var parts = DiffLib.diffLines(orig, fixed);
            var leftHtml = '', rightHtml = '';
            parts.forEach(function (p) {
                var lines = p.value.split('\n');
                if (lines.length && lines[lines.length - 1] === '') lines.pop();
                lines.forEach(function (ln) {
                    var safe = _afixEscape(ln) + '\n';
                    if (p.added) {
                        rightHtml += '<span class="ln ln-add">' + safe + '</span>';
                    } else if (p.removed) {
                        leftHtml += '<span class="ln ln-del">' + safe + '</span>';
                    } else {
                        leftHtml += '<span class="ln ln-ctx">' + safe + '</span>';
                        rightHtml += '<span class="ln ln-ctx">' + safe + '</span>';
                    }
                });
            });
            leftEl.innerHTML = leftHtml;
            rightEl.innerHTML = rightHtml;
        }''',
r'''        function _afixNumberedLines(text, cls) {
            var lines = text.split('\n');
            if (lines.length && lines[lines.length - 1] === '') lines.pop();
            var html = '';
            lines.forEach(function (ln, i) {
                var safe = _afixEscape(ln) + '\n';
                html += '<div class="autofix-row"><span class="autofix-ln">' + (i + 1) + '</span><span class="ln ' + cls + ' autofix-code">' + safe + '</span></div>';
            });
            return html;
        }

        function _afixRender() {
            var DiffLib = window.Diff || window.jsdiff;
            if (!DiffLib || !DiffLib.diffLines) {
                var leftEl = document.getElementById('autofix-original');
                var rightEl = document.getElementById('autofix-code');
                if (leftEl) leftEl.innerHTML = _afixNumberedLines(window._autofix.original || '', 'ln-ctx');
                if (rightEl) rightEl.innerHTML = _afixNumberedLines(window._autofix.fixed || '', 'ln-add');
                return;
            }
            var leftEl = document.getElementById('autofix-original');
            var rightEl = document.getElementById('autofix-code');
            if (!leftEl || !rightEl) return;
            var orig = window._autofix.original || '';
            var fixed = window._autofix.fixed || '';
            if (typeof Diff === 'undefined' || !Diff.diffLines) {
                leftEl.innerHTML = _afixNumberedLines(orig, 'ln-ctx');
                rightEl.innerHTML = _afixNumberedLines(fixed, 'ln-add');
                return;
            }
            var parts = DiffLib.diffLines(orig, fixed);
            var leftHtml = '', rightHtml = '';
            var leftLn = 0, rightLn = 0;
            parts.forEach(function (p) {
                var lines = p.value.split('\n');
                if (lines.length && lines[lines.length - 1] === '') lines.pop();
                lines.forEach(function (ln) {
                    var safe = _afixEscape(ln) + '\n';
                    var row = function(lnNum, cssClass, content) {
                        return '<div class="autofix-row"><span class="autofix-ln">' + lnNum + '</span><span class="ln ' + cssClass + ' autofix-code">' + content + '</span></div>';
                    };
                    if (p.added) {
                        rightLn++;
                        rightHtml += row(rightLn, 'ln-add', safe);
                    } else if (p.removed) {
                        leftLn++;
                        leftHtml += row(leftLn, 'ln-del', safe);
                    } else {
                        leftLn++;
                        rightLn++;
                        leftHtml += row(leftLn, 'ln-ctx', safe);
                        rightHtml += row(rightLn, 'ln-ctx', safe);
                    }
                });
            });
            leftEl.innerHTML = leftHtml;
            rightEl.innerHTML = rightHtml;
        }'''))

# ---------------------------------------------------------------------------
# Edit 3: Fix saveFixedCode() to exclude line numbers from saved content
# ---------------------------------------------------------------------------
edits.append((r'''        function saveFixedCode() {
            var pane = document.getElementById('autofix-code');
            var fixed = pane ? pane.innerText : (window._autofix.fixed || '');
            if (!fixed) { alert('No fixed code to save.'); return; }''',
r'''        function saveFixedCode() {
            var pane = document.getElementById('autofix-code');
            var fixed = '';
            if (pane) {
                var codeSpans = pane.getElementsByClassName('autofix-code');
                if (codeSpans.length > 0) {
                    fixed = Array.from(codeSpans).map(function (s) { return s.textContent; }).join('');
                } else {
                    fixed = pane.innerText;
                }
            }
            fixed = fixed || (window._autofix.fixed || '');
            if (!fixed) { alert('No fixed code to save.'); return; }'''))

# ---------------------------------------------------------------------------
# Apply all edits
# ---------------------------------------------------------------------------
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
print("\nDone — line numbers added to both Auto Fix diff panes.")
'@ | Set-Content -Path $pyScript -Encoding UTF8

# Run the Python edit script
python $pyScript

Write-Host "`nDone. Refresh ACEsi in your browser to see line numbers in the diff modal."
