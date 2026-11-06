import ast

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the list part only (after the =)
start = content.find('TOOLS_SCHEMA = [')
eq_pos = content.find('=', content.find('TOOLS_SCHEMA = ['))
list_start = content.find('[', eq_pos)

bracket_count = 0
in_string = False
escape = False
quote_char = None
end = len(content)
for i, ch in enumerate(content[list_start:], start=0):
    abs_idx = list_start + i
    if not in_string:
        if ch in '"\'':
            in_string = True
            quote_char = ch
        elif ch == '[':
            bracket_count += 1
        elif ch == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end = abs_idx + 1
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
    end = len(content)

list_text = content[list_start:end]
print(f"List text length: {len(list_text)}")
print(f"First 50 chars: {repr(list_text[:50])}")
print(f"Last 50 chars: {repr(list_text[-50:])}")

try:
    tree = ast.parse(list_text, mode='eval')
    print("Compile OK")
    schema_list = eval(compile(list_text, '<string>', 'eval'))
    print(f"Length: {len(schema_list)}")
    names = [item['function']['name'] for item in schema_list]
    print(f"run_command in list: {'run_command' in [item['function']['name'] for item in schema_list]}")
    for i, name in enumerate(names):
        print(f"  {i}: {name}")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    print(f"Error at line {e.lineno}, offset {e.offset}")
    lines = list_text.split('\n')
    for i, line in enumerate(lines):
        if i >= max(0, e.lineno - 5) and i <= min(len(lines) - 1, e.lineno + 3):
            marker = ">>> " if i == e.lineno - 1 else "    "
            print(f"{marker}{i+1}: {repr(line)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()