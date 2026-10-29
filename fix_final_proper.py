with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the insertion point
idx = content.find('full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)')
if idx == -1:
    print("Start marker not found")
    exit(1)

insert_idx = content.find('\n    # Compact schema for net-domain tools', content.find('full_domain_schema = _filter_tools_schema'))
if idx == -1:
    print("Insertion point not found")
    exit(1)

insertion = '''
    # Ensure run_command is in the schema if allowed (workaround for parsing issue)
    if "run_command" in allowed_names and not any(t["function"]["name"] == "run_command" for t in full_domain_schema):
        run_cmd_tool = {"type": "function", "function": {"name": "run_command",
            "description": "Run a shell command and return stdout/stderr. Args: command.",
            "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}
        full_domain_schema.append(run_cmd_tool)
    # DEBUG
    try:
        with open("C:/Users/chris/StudentSyncSA/debug_schema.txt", "a", encoding="utf-8") as f:
            newline = "\n"
            f.write(f"full_domain_schema: {len(full_domain_schema)} tools: {[t['function']['name'] for t in full_domain_schema]}" + newline)
            f.write(f"  run_command in full_domain_schema: {'run_command' in [t['function']['name'] for t in full_domain_schema]}" + newline)
            f.write(f"  allowed_names at filter time: {sorted(allowed_names)}" + newline)
            f.write(f"  run_command in allowed_names: {'run_command' in allowed_names}" + newline)
        except:
            pass

'''

insert_idx = content.find('\n    # Compact schema for net-domain tools', content.find('full_domain_schema = _filter_tools_schema'))
if idx == -1:
    print("Insertion point not found")
    exit(1)

content = content[:idx] + insertion + content[idx:]

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed successfully")