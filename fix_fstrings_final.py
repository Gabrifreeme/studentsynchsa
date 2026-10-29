with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the DEBUG block for full_domain_schema
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)' in line:
        start_idx = i
        break

if start_idx == -1:
    print("Start marker not found")
    exit(1)

# Find the DEBUG block after this
debug_idx = -1
for i in range(start_idx, len(lines)):
    if lines[i].strip() == '# DEBUG':
        debug_idx = i
        break

if debug_idx == -1:
    print("DEBUG not found")
    exit(1)

# Find the except:pass block
except_idx = -1
for i in range(debug_idx, len(lines)):
    if lines[i].strip() == 'except:':
        except_idx = i
        break

if except_idx == -1:
    print("except not found")
    exit(1)

# Find the 'pass' line
pass_idx = -1
for i in range(except_idx, len(lines)):
    if lines[i].strip() == 'pass':
        pass_idx = i
        break

if pass_idx == -1:
    print("pass not found")
    exit(1)

# The block to replace is from debug_idx to pass_idx (inclusive)
old_lines = lines[debug_idx:pass_idx+1]

print(f"Old block lines {debug_idx+1}-{pass_idx+1}:")
for i, line in enumerate(lines[debug_idx:pass_idx+1]):
    print(f"  {debug_idx+i+1}: {repr(lines[debug_idx+i])}")

new_lines = [
    '    # DEBUG\n',
    '    try:\n',
    '        with open("C:/Users/chris/StudentSyncSA/debug_schema.txt", "a", encoding="utf-8") as f:\n',
    '            f.write(f"full_domain_schema: {len(full_domain_schema)} tools: {[t[\'function\'][\'name\'] for t in full_domain_schema]}" + "\\n")\n',
    '            f.write(f"  run_command in full_domain_schema: {\'run_command\' in [t[\'function\'][\'name\'] for t in full_domain_schema]}" + "\\n")\n',
    '            f.write(f"  allowed_names at filter time: {sorted(allowed_names)}" + "\\n")\n',
    '            f.write(f"  run_command in allowed_names: {\"run_command\" in allowed_names}" + "\\n")\n',
    '        except:\n',
    '            pass\n'
]

print(f"Old block length: {len(lines[debug_idx:pass_idx+1])} lines")
print(f"New block length: {len(new_lines)} lines")

# Replace
new_lines = lines[:debug_idx] + new_lines + lines[pass_idx+1:]

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed successfully")