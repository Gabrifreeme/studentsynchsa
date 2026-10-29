import re

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''def _filter_tools_schema(schema, allowed_names):
    # DEBUG
    try:
        with open("C:/Users/chris/StudentSyncSA/debug_filter.txt", "a", encoding="utf-8") as f:
            f.write(f"_filter_tools_schema: schema size={len(schema)}, allowed_names size={len(allowed_names)}\\n")
            f.write(f"  run_command in allowed_names: {'run_command' in allowed_names}\\n")
            f.write(f"  run_command in schema: {any(t['function']['name'] == 'run_command' for t in schema)}\\n")
    except:
        pass
    result = [t for t in schema if t["function"]["name"] in allowed_names]
    # DEBUG
    try:
        with open("C:/Users/chris/StudentSyncSA/debug_filter.txt", "a", encoding="utf-8") as f:
            f.write(f"_filter_tools_schema result: {len(result)} tools, run_command in result: {'run_command' in [t['function']['name'] for t in result]}\\n")
    except:
        pass
    return result'''

new = '''def _filter_tools_schema(schema, allowed_names):
    # DEBUG
    try:
        with open("C:/Users/chris/StudentSyncSA/debug_filter.txt", "a", encoding="utf-8") as f:
            f.write(f"_filter_tools_schema: schema size={len(schema)}, allowed_names size={len(allowed_names)}\\n")
            f.write(f"  run_command in allowed_names: {'run_command' in allowed_names}\\n")
            f.write(f"  run_command in schema: {any(t['function']['name'] == 'run_command' for t in schema)}\\n")
            f.write(f"  schema id: {id(schema)}, TOOLS_SCHEMA id: {id(TOOLS_SCHEMA)}\\n")
    except:
        pass
    result = [t for t in schema if t["function"]["name"] in allowed_names]
    # DEBUG
    try:
        with open("C:/Users/chris/StudentSyncSA/debug_filter.txt", "a", encoding="utf-8") as f:
            f.write(f"_filter_tools_schema result: {len(result)} tools, run_command in result: {'run_command' in [t['function']['name'] for t in result]}\\n")
    except:
        pass
    return result'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed successfully")
else:
    print("OLD NOT FOUND")
    # Try to find it
    idx = content.find('def _filter_tools_schema')
    if idx >= 0:
        print("Found at index:", idx)
        print(content[idx:idx+500])