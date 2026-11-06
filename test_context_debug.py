import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')

import yaml

config_path = r'C:\Users\chris\StudentSyncSA\ace_config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Test _context_tool_policy for "code" context
ctx = config.get('contexts', {}).get('code', {})
print(f"Code context: {ctx}")

caps_name = ctx.get('tool_caps')
print(f"tool_caps: {caps_name}")

caps = config.get('tool_caps', {}).get(caps_name) if caps_name else None
print(f"caps: {caps}")

if caps:
    allowed = caps.get('allowed')
    tools = set(caps.get('tools') or [])
    print(f"allowed domains: {allowed}")
    print(f"tools: {sorted(tools)}")
    print(f"run_command in tools: {'run_command' in tools}")

# Now test the actual function
import server

# Test _context_tool_policy
ctx_domains, ctx_tools = server._context_tool_policy("code")
print(f"\n_context_tool_policy('code'):")
print(f"  allowed domains: {ctx_domains}")
print(f"  tools: {sorted(ctx_tools) if ctx_tools else None}")
print(f"  run_command in tools: {'run_command' in ctx_tools if ctx_tools else False}")

# Test domain tools
code_domain_tools = server._domain_tool_names("code")
print(f"\nDomain tools for 'code': {sorted(code_domain_tools)}")

# Test intersection
if ctx_tools:
    intersection = code_domain_tools & ctx_tools
    print(f"\nIntersection: {sorted(intersection)}")
    print(f"run_command in intersection: {'run_command' in intersection}")