import re

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('TOOLS_SCHEMA = [')
if start == -1:
    print("TOOLS_SCHEMA not found")
    exit(1)

eq_pos = content.find('=', content.find('TOOLS_SCHEMA = ['))
list_start = content.find('[', content.find('TOOLS_SCHEMA = ['))

bracket_count = 0
in_string = False
escape = False
quote_char = None
end = len(content)
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
names = re.findall(r'"name": "([^"]+)"', list_text)
print(f"Length: {len(names)}")
print("run_command in list:", "run_command" in names)
for i, name in enumerate(names):
    print(f"  {i}: {name}")