with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    # DEBUG
    try:
        with open("C:/Users/chris/StudentSyncSA/debug_schema.txt", "a", encoding="utf-8") as f:
            f.write(f"full_domain_schema: {len(full_domain_schema)} tools: {[t['function']['name'] for t in full_domain_schema]}\n")
            f.write(f"  run_command in full_domain_schema: {'run_command' in [t['function']['name'] for t in full_domain_schema]}\n")
            f.write(f"  allowed_names at filter time: {sorted(allowed_names)}\n")
            f.write(f"  run_command in allowed_names: {'run_command' in allowed_names}\n")
        except:
            pass'''

new = '''    # DEBUG
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