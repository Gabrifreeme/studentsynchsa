with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the DEBUG block for full_domain_schema
idx = content.find('full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)')
if idx == -1:
    print("Marker not found")
    exit(1)

# Find the DEBUG block after this
debug_idx = content.find('# DEBUG', idx)
if debug_idx == -1:
    print("DEBUG not found")
    exit(1)

# Find the except:pass block end
except_idx = content.find('except:', debug_idx)
if except_idx == -1:
    print("except not found")
    exit(1)
except_end = content.find('pass', except_idx)
if except_end == -1:
    print("pass not found")
    exit(1)
except_end += 4  # len('pass')

old_block = content[content.find('full_domain_schema = _filter_tools_schema'):except_end+4]

print(f"Old block length: {len(old_block)}")
print("Old block preview:")
print(repr(old_block[:500]))

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
            f.write(f"full_domain_schema: {len(full_domain_schema)} tools: {[t[\"function\"][\"name\"] for t in full_domain_schema]}\n")
            f.write(f"  run_command in full_domain_schema: {\"run_command\" in [t[\"function\"][\"name\"] for t in full_domain_schema]}\n")
            f.write(f"  allowed_names at filter time: {sorted(allowed_names)}\n")
            f.write(f"  run_command in allowed_names: {\"run_command\" in allowed_names}\n")
        except:
            pass'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed successfully")
else:
    print("OLD NOT FOUND")
    idx = content.find('# DEBUG')
    if idx >= 0:
        print("Found DEBUG at:", idx)
        print(repr(content[idx:idx+500]))