path = 'ACEsi.html'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Replace the exact broken strings from your screenshot
content = content.replace('0ÿZ¤', '🎤')
content = content.replace('0ÿS', '🔊')
content = content.replace('až', '➕')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Buttons fixed!")