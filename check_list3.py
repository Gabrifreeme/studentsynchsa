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
                end = i + 1
                break
    elif escape:
        escape = False
    elif ch == '\\':
        escape = True
    elif ch == quote_char:
        in_string = False
        quote_char = None

list_text = content[start:end]

# Check for run_command
idx = list_text.find('run_command')
if idx >= 0:
    print(f'Found run_command at index {idx}')
    print(repr(list_text[max(0,idx-100):idx+200]))
else:
    print('run_command NOT found in list text')
    # Check what's between curl and notify
    curl_idx = list_text.find('curl')
    if curl_idx >= 0:
        notify_idx = list_text.find('notify', curl_idx)
        if notify_idx >= 0:
            print('Text between curl and notify:')
            print(repr(list_text[curl_idx:notify_idx+200]))