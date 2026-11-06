import ast

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('TOOLS_SCHEMA = [')
list_start = content.find('[', content.find('=', content.find('TOOLS_SCHEMA = [')))

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
    else:
        if escape:
            escape = False
        elif ch == '\\':
            escape = True
        elif ch == quote_char:
            in_string = False
            quote_char = None

list_text = content[start:end]

# Find curl and run_command in the list text
curl_idx = list_text.find('curl')
run_idx = list_text.find('run_command')

print(f"curl found at: {curl_idx}")
print(f"run_command found at: {list_text.find('run_command')}")

if curl_idx >= 0:
    # Print context around curl
    print("Context around curl:")
    print(repr(list_text[max(0, curl_idx-100):curl_idx+500]))

# Also check the exact bytes between curl and run_command
curl_end = list_text.find('}}},\n', list_text.find('curl'))
if curl_end >= 0:
    next_item_start = list_text.find('{', curl_end)
    print(f"\nText between curl and next item:")
    print(repr(list_text[curl_end:next_item_start+100]))