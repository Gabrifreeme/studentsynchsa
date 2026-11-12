import io, re
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    html = f.read()

matches = []
for m in re.finditer(r'fetch\(["\']http://127\.0\.0\.1:5000/memory/set["\']', html):
    start = max(0, m.start() - 700)
    end = min(len(html), m.end() + 500)
    matches.append((m.start(), html[start:end]))

if len(matches) >= 2:
    print(f"Second /memory/set call context:")
    print("=" * 60)
    print(matches[1][1])
    print("=" * 60)
else:
    print(f"Only {len(matches)} /memory/set call(s) found")
