import ast

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('TOOLS_SCHEMA = [')
if start == -1:
    print("TOOLS_SCHEMA not found")
else:
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
        else:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote_char:
                in_string = False
                quote_char = None

    list_text = content[list_start:end]
    print(f"List text length: {len(list_text)}")
    
    # Try to parse just the list
    try:
        tree = ast.parse(list_text, mode='eval')
        print("Syntax OK")
        schema_list = eval(compile(list_text, '<string>', 'eval'))
        print(f"Length: {len(schema_list)}")
        names = [item['function']['name'] for item in schema_list]
        for i, name in enumerate(names):
            print(f"  {i}: {name}")
        print(f"\nrun_command in list: {'run_command' in [item['function']['name'] for item in schema_list]}")
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