import re

with open('C:\\Users\\chris\\StudentSyncSA\\ACEsi.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the main script
match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
if match:
    script = match.group(1)
    # Find all single-quoted strings
    strings = re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", script)
    for s in strings:
        if '{' in s or '}' in s:
            print('Brace in string:', s[:120])