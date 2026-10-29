import ast

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('TOOLS_SCHEMA = [')
eq_pos = content.find('=', content.find('TOOLS_SCHEMA = ['))
list_start = content.find('[', eq_pos)

bracket_count = 0
in_string = False
escape = False
quote_char = None
end = len(content)
for i, ch in enumerate(content[list_start:], start=list_start):
    if not in_string:
        if ch in '"\'':
            in_string = True
            quote_char = ch
        elif ch == '[':
            bracket_count += 1
        elif ch == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end = i + 1
                break
    else:
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == quote_char:
            in_string = False
            quote_char = None

list_text = content[start:end]

# Find curl and notify in the list text
curl_idx = list_text.find('curl')
notify_idx = list_text.find('notify', curl_idx)
if curl_idx >= 0 and notify_idx >= 0:
    between = list_text[curl_idx:notify_idx+200]
    print('Text between curl and notify:')
    print(repr(list_text[max(0,curl_idx-100):notify_idx+200]))