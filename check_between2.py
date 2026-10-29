with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('TOOLS_SCHEMA = [')
eq_pos = content.find('=', start)
list_start = content.find('[', start)

bracket_count = 0
in_string = False
escape = False
quote_char = None
end = start
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
                break
    else:
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == quote_char:
            in_string = False
            quote_char = None
    else:
        end = i + 1

list_text = content[start:end]

curl_idx = list_text.find('curl')
notify_idx = list_text.find('notify', curl_idx)
if curl_idx >= 0 and notify_idx >= 0:
    print('Text between curl and notify:')
    print(repr(list_text[curl_idx:notify_idx+200]))