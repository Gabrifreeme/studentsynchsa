import ast

# Test parsing just the curl to notify section
test_text = '''[
    {"type": "function", "function": {"name": "curl",
        "description": "Hit a URL and return HTTP status + body snippet. ok=False = no service/port closed. Args: url (https), timeout optional.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}, "timeout": {"type": "number"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "run_command",
        "description": "Run a shell command and return stdout/stderr. Args: command.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "notify",
        "description": "Send a push notification to Chris's phone via ntfy. Use when Chris asks to 'ping my phone', 'notify me'. Args: message (text), title optional.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}}
]'''

try:
    tree = ast.parse(test_text, mode='eval')
    print("Syntax OK")
    schema_list = eval(compile(test_text, '<string>', 'eval'))
    print(f"Length: {len(schema_list)}")
    names = [item['function']['name'] for item in test_list]
    print(f"run_command in list: {'run_command' in [item['function']['name'] for item in test_list]}")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    print(f"Error at line {e.lineno}, offset {e.offset}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()