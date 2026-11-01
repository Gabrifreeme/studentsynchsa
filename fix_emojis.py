# fix_emojis.py
path = 'ACEsi.html'

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# The exact broken strings we saw in the error log
content = content.replace('âœ…', '✅')
content = content.replace('âŒ', '❌')

# The bottom buttons (Mojibake)
content = content.replace('0ÿZ¤', '🎤')
content = content.replace('0ÿS', '🔊')
content = content.replace('až', '➕')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("File fixed and saved as UTF-8!")