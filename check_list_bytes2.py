with open(r'C:\Users\chris\StudentSyncSA\server.py', 'rb') as f:
    content = f.read()

start = content.find(b'TOOLS_SCHEMA = [')
eq_pos = content.find(b'=', start)
list_start = content.find(b'[', start)

bracket_count = 0
in_string = False
escape = False
quote_char = None
end = start
for i, ch in enumerate(content[list_start:], start=list_start):
    if not in_string:
        if ch in (ord(b'"'), ord(b"'")):
            in_string = True
            quote_char = ch
        elif ch == ord('['):
            bracket_count += 1
        elif ch == ord(']'):
            bracket_count -= 1
            if bracket_count == 0:
                end = i + 1
                break
    else:
        if escape:
            escape = False
        elif ch == ord(b'\\'):
            escape = True
        elif ch == quote_char:
            in_string = False
            quote_char = None
else:
    end = len(content)

list_bytes = content[list_start:end]
print(f'List length: {len(list_bytes)}')

# Find run_command in the list
idx = list_bytes.find(b'run_command')
if idx >= 0:
    print(f'Found run_command at list byte index {idx}')
    print(repr(list_bytes[max(0,idx-100):idx+200]))
else:
    print('run_command NOT found in list bytes')
    # Find curl
    curl_idx = list_bytes.find(b'curl')
    if curl_idx >= 0:
        print(f'curl at list byte index {curl_idx}')
        # Find next tool after curl
        next_tool = list_bytes.find(b'{"name":', idx + 10)
        if next_tool >= 0:
            print(f'Next tool at list byte index {next_tool}')
            print(repr(list_bytes[next_tool:next_tool+100]))