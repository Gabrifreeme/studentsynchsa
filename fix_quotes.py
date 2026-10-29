with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find and fix the memory injection code - replace curly/smart quotes with regular quotes
# The issue is that smart quotes (\" ") got mangled during file operations

# Look for the memory note pattern and fix the quotes
old_pattern = '�Memory note: � + open(_SETTINGS_PATH.replace(�config.json�, �memory.txt�), �r�, encoding=�utf-8�, errors=�replace�).read().strip() if os.path.exists(_SETTINGS_PATH.replace(�config.json�, �memory.txt")) else ��)'

# Let me just search for the key parts and ensure they use regular quotes
# First, let me find where the memory injection is and reconstruct with proper quotes

# Find the location of memory injection
idx = content.find('Memory note')
if idx > 0:
    # Show 200 chars around it
    start = max(0, idx - 20)
    end = min(len(content), idx + 200)
    section = content[start:end]
    print('Current memory injection section:')
    print(section[:200])
    
    # Now fix the quotes - replace the mangled parts
    # The pattern has smart quotes that need to be regular quotes
    fixed = section.replace('�config.json�', '"config.json"')
    fixed = fixed.replace('�memory.txt�', '"memory.txt"')
    fixed = fixed.replace('�r�', 'r"')
    fixed = fixed.replace('�utf-8�', '"utf-8"')
    fixed = fixed.replace('�replace�', '"replace"')
    fixed = fixed.replace('�Memory note�', 'Memory note')
    fixed = fixed.replace('�Memory note: �', 'Memory note: ')
    fixed = fixed.replace(' else ��)', ')')
    
    # Replace the original section with fixed version
    content = content[:start] + fixed + content[end:]
    
    with open('C:/Users/chris/LipSyncStudent/server.py', 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    
    print('Fixed quotes in memory injection code')
else:
    print('Memory note section not found - checking alternate pattern')
    # Try finding just the open() call
    idx2 = content.find('open(_SETTINGS_PATH.replace')
    if idx2 > 0:
        print('Found open() call at', idx2)