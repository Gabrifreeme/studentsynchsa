with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''"cdp_connect": (tool_cdp_connect, ()),
         # "cdp_navigate": (tool_cdp_navigate, ("url",)),  # DISABLED: force use of web_search API,
    "cdp_evaluate": (tool_cdp_evaluate, ("expr",)),
    "cdp_console_logs": (tool_cdp_console_logs, ()),
    "cdp_dom_state": (tool_cdp_dom_state, ()),
    "cdp_network_requests": (tool_cdp_network_requests, ()),
    "cdp_get_response_body": (tool_cdp_get_response_body, ()),
    "cdp_status": (tool_cdp_status, ()),'''

new = '''"cdp_connect": (tool_cdp_connect, ()),
         # "cdp_navigate": (tool_cdp_navigate, ("url",)),  # DISABLED: force use of web_search API,
    "cdp_console_logs": (tool_cdp_console_logs, ()),
    "cdp_dom_state": (tool_cdp_dom_state, ()),
    "cdp_get_response_body": (tool_cdp_get_response_body, ()),
    "cdp_status": (tool_cdp_status, ()),'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("TOOLS dict patched successfully")
else:
    print("OLD TEXT NOT FOUND")