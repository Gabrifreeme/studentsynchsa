import sys
import os

# Add the directory to path
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')

# Try to compile just the TOOLS_SCHEMA part
with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract just the TOOLS_SCHEMA definition
start = content.find('TOOLS_SCHEMA = [')
list_start = content.find('[', content.find('=', content.find('TOOLS_SCHEMA = [')))

bracket_count = 0
in_string = False
escape = False
quote_char = None
end = start
for i, ch in enumerate(content[content.find('[', content.find('=', content.find('TOOLS_SCHEMA = [')):], start=content.find('[', content.find('=', content.find('TOOLS_SCHEMA = [')))):
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
    else:
        end = len(content)

list_text = content[start:end]

# Try to compile just the list
try:
    code = compile(list_text, '<string>', 'eval')
    schema_list = eval(list_text)
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