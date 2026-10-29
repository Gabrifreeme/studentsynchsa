with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section to replace
marker = 'full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)'
idx = content.find(marker)
if idx == -1:
    print("Marker not found")
    exit(1)

# Find the end of the DEBUG block
search_start = content.find('# DEBUG', content.find('full_domain_schema = _filter_tools_schema'))
if search_start == -1:
    search_start = content.find('# DEBUG', content.find('full_domain_schema = _filter_tools_schema'))

# Find the end of the DEBUG block
block_end = content.find('except:\n        pass\n', search_start)
if block_end == -1:
    block_end = content.find('except:\n        pass\n', search_start)

if block_end == -1:
    print("Could not find block end")
    exit(1)

block_end += len('except:\n        pass\n')

old_block = content[content.find('full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)'):block_end]

new_block = '''full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)
    # Ensure run_command is in the schema if allowed (workaround for parsing issue)
    if "run_command" in allowed_names and not any(t["function"]["name"] == "run_command" for t in full_domain_schema):
        run_cmd_tool = {"type": "function", "function": {"name": "run_command",
            "description": "Run a shell command and return stdout/stderr. Args: command.",
            "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}
        full_domain_schema.append(run_cmd_tool)
    # DEBUG
    try:
        with open("C:/Users/chris/StudentSyncSA/debug_schema.txt", "a", encoding="utf-8") as f:
            f.write(f"full_domain_schema: {len(full_domain_schema)} tools: {[t['function']['name'] for t in full_domain_schema]}\n")
            f.write(f"  run_command in full_domain_schema: {'run_command' in [t['function']['name'] for t in full_domain_schema]}\n")
            f.write(f"  allowed_names at filter time: {sorted(allowed_names)}\n")
            f.write(f"  run_command in allowed_names: {'run_command' in allowed_names}\n")
        except:
            pass'''

print(f"Old block length: {len(old_block)}")
print(f"New block length: {len(new_block)}")

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed successfully")
else:
    print("OLD BLOCK NOT FOUND")
    # Debug
    idx = content.find('full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)')
    if idx >= 0:
        print("Found at:", idx)
        print(repr(content[idx:idx+500]))