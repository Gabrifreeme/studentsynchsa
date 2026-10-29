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
except_idx = -1
pass_idx = -1
for i in range(len(lines)):
    if lines[i].strip() == 'except:' and i > 0 and lines[i-1].strip() == 'pass':
        except_idx = i
        pass_idx = i-1
        break

if pass_idx == -1:
    print("pass not found")
    exit(1)

# Fix the indentation
lines[pass_idx] = '        pass\n'  # 8 spaces (inside except block)
lines[pass_idx - 1] = '    except:\n'  # 4 spaces (same as try:)

print("Fixed indentation")

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed successfully")