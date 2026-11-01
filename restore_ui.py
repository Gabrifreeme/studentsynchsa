with open('ACEsi.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix buttons
html = html.replace('0ÿZ¤', '🎤')
html = html.replace('0ÿS', '🔊')
html = html.replace('až', '➕')
html = html.replace('až•', '➕')

# Fix timer color
html = html.replace('color:#e0e0e0;', 'color:#ff9d00;')

# Fix checkmarks
html = html.replace('âœ…', '✅')
html = html.replace('âŒ', '❌')

with open('ACEsi.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("UI restored perfectly!")