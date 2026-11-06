with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the TOOLS_SCHEMA list start
start = content.find('TOOLS_SCHEMA = [')
list_start = content.find('[', content.find('=', content.find('TOOLS_SCHEMA = [')))

# Find the run_command in the full content
run_cmd_idx = content.find('run_command', content.find('curl', content.find('TOOLS_SCHEMA = [')))

# Find the list end by bracket counting
bracket_count = 0
in_string = False
escape = False
quote_char = None
list_end = len(content)

for i, ch in enumerate(content[content.find('[', content.find('=', content.find('TOOLS_SCHEMA = ['))):], start=content.find('[', content.find('=', content.find('TOOLS_SCHEMA = [')))):
    if not in_string:
        if ch in '"\'':
            in_string = True
            quote_char = ch
        elif ch == '[':
            bracket_count += 1
        elif ch == ']':
            bracket_count -= 1
            if bracket_count == 0:
                list_end = i + 1
                break
        else:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote_char:
                in_string = False
                quote_char = None

print(f"List start: {content.find('TOOLS_SCHEMA = [')}")
print(f"List end (by bracket counting): {list_end}")
print(f"run_command index: {content.find('run_command', content.find('curl', content.find('TOOLS_SCHEMA = [')))}")

# Check for ] between curl and run_command
curl_idx = content.find('curl', content.find('TOOLS_SCHEMA = ['))
run_cmd_idx = content.find('run_command', content.find('curl', content.find('TOOLS_SCHEMA = [')))
if curl_idx >= 0 and run_cmd_idx >= 0:
    between = content[curl_idx:run_cmd_idx]
    # Find any ] in between
    bracket_positions = [i for i, ch in enumerate(between) if ch == ']']
    print(f"Found {len(bracket_positions)} ] characters between curl and run_command")
    for pos in bracket_positions[:10]:
        context_start = max(0, pos-50)
        context_end = min(len(between), pos+50)
        print(f"  ] at offset {pos}: ...{repr(between[context_start:context_end])}...")