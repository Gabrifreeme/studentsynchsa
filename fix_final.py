with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the DEBUG block for full_domain_schema
debug_idx = -1
for i, line in enumerate(lines):
    if 'full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)' in line:
        for j in range(i+1, len(lines)):
            if lines[j].strip() == '# DEBUG':
                debug_idx = j
                break
        break

if debug_idx == -1:
    print("DEBUG block not found")
    exit(1)

# Find the end of the try/except block
pass_idx = -1
for i in range(debug_idx, len(lines)):
    if lines[i].strip() == 'pass' and i > 0 and lines[i-1].strip() == 'except:':
        pass_idx = i
        break

if pass_idx == -1:
    print("pass not found")
    exit(1)

# Replace lines from debug_idx to pass_idx (inclusive)
old_lines = lines[debug_idx:pass_idx+1]

new_lines = [
    '    # DEBUG\n',
    '    try:\n',
    '        with open("C:/Users/chris/StudentSyncSA/debug_schema.txt", "a", encoding="utf-8") as f:\n',
    '            newline = "\\n"\n',
    '            f.write(f"full_domain_schema: {len(full_domain_schema)} tools: {[t[\'function\'][\'name\'] for t in full_domain_schema]}" + newline)\n',
    '            f.write(f"  run_command in full_domain_schema: {\'run_command\' in [t[\'function\'][\'name\'] for t in full_domain_schema]}" + "\\n")\n',
    '            f.write(f"  allowed_names at filter time: {sorted(allowed_names)}" + "\\n")\n',
    '            f.write(f"  run_command in allowed_names: {\"run_command\" in allowed_names}" + "\\n")\n',
    '        except:\n',
    '            pass\n'
]

# Replace
new_lines = lines[:debug_idx] + new_lines + lines[pass_idx+1:]

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed successfully")