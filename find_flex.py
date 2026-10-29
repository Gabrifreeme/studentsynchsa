path = "C:\\Users\\chris\\LipSyncStudent\\ACESi.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Find the chat input flex div (has border-top)
import re
# Find all occurrences of display:flex
for m in re.finditer(r'display:flex', content):
    idx = m.start()
    snippet = content[idx:idx+200]
    if 'chat-input' in snippet or 'border-top' in snippet:
        print(f"Index {idx}: {repr(snippet[:200])}")
