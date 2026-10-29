with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Move tool_get_distance before the TOOLS dict
old = '''    "get_distance": (tool_get_distance, ("origin", "destination")),
}


def tool_get_distance(origin, destination):'''

new = '''def tool_get_distance(origin, destination):'''

content = content.replace(old, new)

# Now add the entry to the TOOLS dict
old2 = '''    "forget_preference": (tool_forget_preference, ("key",)),
}'''
new2 = '''    "forget_preference": (tool_forget_preference, ("key",)),
    "get_distance": (tool_get_distance, ("origin", "destination")),
}'''
content = content.replace(old2, new2)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done - tool_get_distance moved before TOOLS dict')