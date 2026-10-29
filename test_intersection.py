import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')

# Test the context tool policy using the server's actual _ACE_CONTEXTS
import yaml
config_path = r'C:\Users\chris\StudentSyncSA\ace_config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

_ACE_CONFIG = config
_ACE_CONTEXTS = config.get('contexts', {})

def _dom_set(dom):
    if isinstance(dom, str):
        return {dom}
    return set(dom or ())

def _context_tool_policy(ctx_name):
    ctx = (_ACE_CONTEXTS or {}).get(ctx_name) or {}
    caps_name = ctx.get('tool_caps')
    caps = (_ACE_CONFIG.get('tool_caps') or {}).get(caps_name) if caps_name else None
    if not caps:
        return None, None
    return caps.get('allowed'), set(caps.get('tools') or [])

def _dom_set(dom):
    if isinstance(dom, str):
        return {dom}
    return set(dom or ())

def _domain_tool_names(domain):
    _TOOL_DOMAINS = {
        "list_files": "code", "read_file": "code", "list_user_files": "code", "read_user_file": "code", "open_user_file": "code", "view_user_file": "code", "grep": "code",
        "write_file": "code", "edit_file": "code", "open_in_vscode": "code", "run_command": "code",
        "git_status": "code", "git_log": "code", "git_commit": "code",
        "git_branch": "code", "git_merge": "code",
        "build_apk": "code", "pub_add": "code", "pub_remove": "code",
        "pub_upgrade": "code", "flutter_test": "code", "flutter_analyze": "code",
        "ui_device": "ui", "ui_connect": "ui", "ui_app_open": "ui", "ui_tap": "ui", "ui_swipe": "ui",
        "ui_type": "ui", "ui_key": "ui", "ui_dump": "ui", "ui_screenshot": "ui",
        "ui_assert_text": "ui", "ui_assert_element": "ui", "ui_assert_visible": "ui",
        "ui_expect": "ui", "ui_test_run": "ui",
        "cdp_connect": "ui", "cdp_console_logs": "ui",
        "cdp_dom_state": "ui", "cdp_get_response_body": ("ui", "net"), "cdp_status": "ui",
        "curl": "net",
        "notify": "ctrl",
        "check_email": "ctrl", "list_email_rules": "ctrl",
        "get_time": "ctrl",
        "web_search": "net", "webfetch": "net", "weather": "net",
        "note": "ctrl", "todo_add": "ctrl", "todo_list": "ctrl", "todo_done": "ctrl", "todo_remove": "ctrl",
        "set_preference": "ctrl", "list_preferences": "ctrl", "forget_preference": "ctrl",
        "view_web_image": "net", "view_user_file": "code", "open_in_vscode": "code",
        "restart": "ctrl",
    }
    if domain == "general":
        return {n for n, d in _TOOL_DOMAINS.items() if _dom_set(d) & {"code", "net", "ctrl"}}
    return {n for n, d in _TOOL_DOMAINS.items() if domain in _dom_set(d)}

# Test
ctx_domains, ctx_tools = _context_tool_policy("code")
print(f"Context tools for 'code': {sorted(ctx_tools)}")
print(f"run_command in ctx_tools: {'run_command' in ctx_tools}")

code_domain_tools = _domain_tool_names("code")
print(f"\nCode domain tools: {sorted(code_domain_tools)}")
print(f"run_command in code domain: {'run_command' in code_domain_tools}")

intersection = code_domain_tools & ctx_tools
print(f"\nIntersection: {sorted(intersection)}")
print(f"run_command in intersection: {'run_command' in intersection}")
print(f"Intersection size: {len(intersection)}")