import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Find the Add skill function in the Skills manager
# It usually calls fetch('/memory/set', { method: 'POST', body: ... })
old_add = """      async function addSkill() {
        var keyInput = document.getElementById('new-skill-key');
        var valInput = document.getElementById('new-skill-value');
        if (!keyInput || !valInput) return;
        var k = keyInput.value.trim();
        var v = valInput.value.trim();
        if (!k || !v) {
          if (window.showAceToast) window.showAceToast("Key and value required", 'error', 3000);
          return;
        }"""

# We need to see the actual function name first. Let me search for the pattern.
# Actually let's just find every "memory/set" call and inspect
matches = []
for m in re.finditer(r'fetch\(["\']http://127\.0\.0\.1:5000/memory/set["\']', html):
    start = max(0, m.start() - 500)
    end = min(len(html), m.end() + 500)
    matches.append((m.start(), html[start:end]))

if matches:
    print(f"Found {len(matches)} /memory/set call(s). Showing context of first one:")
    print("=" * 60)
    print(matches[0][1])
    print("=" * 60)
else:
    print("No /memory/set calls found")
