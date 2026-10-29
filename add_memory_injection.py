with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the system_prompt construction and add memory.txt injection
# The pattern is: + _mood_softener_line() + \n\n + build_context_block()
old_pattern = '''_mood_softener_line()
            + build_context_block()'''

new_pattern = '''_mood_softener_line()
            + (“Memory note: “ + open(_SETTINGS_PATH.replace(“config.json”, “memory.txt”), “r\”, encoding=“utf-8\”, errors=“replace\”).read().strip() if os.path.exists(_SETTINGS_PATH.replace(“config.json”, “memory.txt\")) else “”)
            + ”\n\n”
            + build_context_block()'''

# Actually, a cleaner approach: add a helper to read memory and inject it
# Let me find a better insertion point

# Let me look for where to add the memory reading code - I'll add a function and call it

# First, let me add a helper function to read memory.txt near the other helper functions
# Find a good location - after _mood_softener_line function

# Actually, let me just inject the memory content directly into the system_prompt construction
# I'll add it right after _mood_softener_line()

search = '''_mood_softener_line()
            + build_context_block()'''

replace = '''_mood_softener_line()
            # Inject memory.txt into system prompt
            try:
                memory_path = _SETTINGS_PATH.replace("config.json", "memory.txt")
                if os.path.exists(memory_path):
                    with open(memory_path, "r", encoding="utf-8", errors="replace") as mf:
                        _memory_content = mf.read().strip()
                else:
                    _memory_content = ""
            except Exception:
                _memory_content = ""
            + _memory_content
            + \n\n
            + build_context_block()'''

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    print('Used new pattern')
else:
    print('Old pattern not found, trying different approach')
    # Try the replace method
    if search in content:
        content = content.replace(search, replace)
        print('Replaced using search pattern')
    else:
        print('Search pattern not found either')
        # Show what's around the area
        idx = content.find('_mood_softener_line()')
        if idx > 0:
            print('Found _mood_softener_line at', idx)
            print(content[idx:idx+200])

with open('C:/Users/chris/LipSyncStudent/server.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print('Memory injection script done')