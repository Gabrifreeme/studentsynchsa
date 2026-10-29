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

# Find the except:pass block
pass_idx = -1
for i in range(debug_idx, len(lines)):
    if lines[i].strip() == 'pass' and i > 0 and lines[i-1].strip() == 'except:':
        pass_idx = i
        break

if pass_idx == -1:
    print("pass not found")
    exit(1)

# Check the except: line indentation
except_idx = pass_idx - 1
while except_idx >= 0 and lines[except_idx].strip() == '':
    except_idx -= 1

if except_idx >= 0 and lines[except_idx].strip() == 'except:':
    # Fix the indentation of except: and pass
    lines[except_idx] = '    except:\n'  # 4 spaces
    lines[pass_idx] = '        pass\n'  # 8 spaces (inside except block)
    print("Fixed indentation")
else:
    print("except not found at expected location")
    exit(1)

# Also fix the f-strings to use proper quoting
for i in range(len(lines)):
    if 'f.write(f"full_domain_schema:' in lines[i]:
        lines[i] = lines[i].replace('f.write(f"full_domain_schema:', 'f.write(f\'full_domain_schema:')
    if 'f.write(f"  run_command in full_domain_schema:' in lines[i]:
        lines[i] = lines[i].replace('f.write(f"  run_command in full_domain_schema:', 'f.write(f\'  run_command in full_domain_schema:')
    if 'f.write(f"  allowed_names at filter time:' in lines[i]:
        lines[i] = lines[i].replace('f.write(f"  allowed_names at filter time:', 'f.write(f\'  allowed_names at filter time:')
    if 'f.write(f"  run_command in allowed_names:' in lines[i]:
        lines[i] = lines[i].replace('f.write(f"  run_command in allowed_names:', 'f.write(f\'  run_command in allowed_names:')

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed successfully")