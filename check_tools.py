import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')

# Execute the server.py up to TOOLS_SCHEMA definition
with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find TOOLS_SCHEMA definition
start = content.find('TOOLS_SCHEMA = [')
if start == -1:
    print("TOOLS_SCHEMA not found")
else:
    # Find the matching closing bracket
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
    print(f"TOOLS_SCHEMA text length: {len(schema_text)}")
    
    # Count items
    import ast
    try:
        schema_list = ast.literal_eval(schema_text)
        print(f"Parsed {len(schema_list)} items")
        names = [item['function']['name'] for item in schema_list]
        print("Tool names:")
        for name in sorted(names):
            print(f"  {name}")
        print(f"\nrun_command in list: {'run_command' in names}")
    except Exception as e:
        print(f"Error parsing: {e}")