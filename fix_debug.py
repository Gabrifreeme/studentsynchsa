with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)'
start_idx = content.find('full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)')
if start_idx == -1:
    print("Start marker not found")
    exit(1)

# Find the DEBUG block start
debug_idx = content.find('# DEBUG', content.find('full_domain_schema = _filter_tools_schema'))
if debug_idx == -1:
    print("DEBUG marker not found")
    exit(1)

# Find the end of the DEBUG block (after 'except:\n            pass\n')
block_end = content.find('except:\n            pass\n', debug_idx)
if block_end == -1:
    block_end = content.find('except:\n            pass\n', content.find('# DEBUG', content.find('full_domain_schema = _filter_tools_schema')))

if block_end == -1:
    print("Could not find block end")
    exit(1)

block_end += len('except:\n            pass\n')

old_block = content[start_idx:block_end + len('except:\n            pass\n')]

print(f"Old block length: {len(old_block)}")
print("Old block preview:")
print(repr(old_block[:200]))