import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# 1. Find the current paste logic we injected and replace it
old_paste_logic = """    var pasteBtn = document.getElementById('terminal-paste-btn');
    if (pasteBtn) {
        pasteBtn.addEventListener('click', function() {
            navigator.clipboard.readText().then(function(text) {
                if (text) {
                    if (typeof _buf !== 'undefined') {
                        _buf += text;
                    }
                    term.write(text);
                }
            }).catch(function(err) {
                console.error('Paste failed:', err);
            });
        });
    }"""

new_paste_logic = """    var pasteBtn = document.getElementById('terminal-paste-btn');
    if (pasteBtn) {
        pasteBtn.addEventListener('click', function() {
            // Create a hidden textarea to capture the paste
            var ta = document.createElement('textarea');
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.focus();
            
            // Trigger native paste
            document.execCommand('paste');
            
            // Grab the text (execCommand paste fills the textarea)
            var text = ta.value;
            document.body.removeChild(ta);
            
            if (text) {
                if (typeof _buf !== 'undefined') {
                    _buf += text;
                }
                term.write(text);
            }
        });
    }"""

if old_paste_logic in html:
    html = html.replace(old_paste_logic, new_paste_logic)
    print("JS: Replaced clipboard API with hidden textarea paste")
else:
    print("JS: WARNING - Could not find old paste logic to replace")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("PATCH COMPLETE")
