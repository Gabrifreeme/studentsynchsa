import ast

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('TOOLS_SCHEMA = [')
if start == -1:
    print("TOOLS_SCHEMA not found")
else:
    bracket_count = 0
    in_string = False
    escape = False
    quote_char = None
    end = start
    for i, ch in enumerate(content[start:], start=start):
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

    schema_text = content[start:end]
    
    # Try to parse just the list
    try:
        tree = ast.parse(schema_text, mode='eval')
        print("Syntax OK")
        # Evaluate
        schema_list = eval(compile(schema_text, '<string>', 'eval'))
        print(f"Length: {len(schema_list)}")
        names = [item['function']['name'] for item in schema_list]
        print(f"run_command in list: {'run_command' in [item['function']['name'] for item in schema_list]}")
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        print(f"Error at line {e.lineno}, offset {e.offset}")
        # Print context around error
        lines = schema_text.split('\n')
        for i, line in enumerate(lines):
            if i >= e.lineno - 3 and i <= e.lineno + 3:
                print(f"{e.lineno + i - e.lineno + 1}: {repr(line)}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()