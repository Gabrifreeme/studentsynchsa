import re

with open(r'C:\Users\chris\StudentSyncSA\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''def _fit_schema_to_budget(messages, tools_schema, max_tokens, budget=_LLM_INPUT_TOKEN_BUDGET):
    """Drop the least important tools until prompt+schema fits the provider cap.

    Providers reject an oversized request with 413 and llm_reply then falls
    through to "all providers unavailable", which looks like an outage but is
    really a payload-size problem. Core tools are never dropped; the rest are
    removed largest-first until the estimated token count fits.
    """
    def est(tools):
        payload = json.dumps({"messages": messages, "tools": tools,
                              "max_tokens": max_tokens})
        return len(payload) // 4

    tools = list(tools_schema)
    if est(tools) <= budget:
        return tools
    # NEVER drop file operation tools - they are critical for local work
    file_tools = {t for t in tools if t["function"]["name"] in _FILE_CORE_TOOLS}
    droppable = [t for t in tools
                 if t["function"]["name"] not in _LLM_CORE_TOOLS]
    # Biggest schemas cost the most tokens, so shed those first.
    droppable.sort(key=lambda t: len(json.dumps(t)), reverse=True)
    for t in droppable:
        if est(tools) <= budget:
            break
        tools.remove(t)
    # If still over budget, we have a problem - but NEVER drop file tools
    if est(tools) > budget:
        print(f"⚠️ Schema still over budget ({est(tools)} > {budget}) after dropping non-core tools")
        print(f"   Keeping {len(tools)} tools including file tools: {[t['function']['name'] for t in tools if t['function']['name'] in _FILE_CORE_TOOLS]}")
    if len(tools) != len(tools_schema):
        print("✂️ schema trimmed %d -> %d tools to fit %d-token budget (est %d)"
              % (len(tools_schema), len(tools), budget, est(tools)))
        remaining = [t["function"]["name"] for t in tools]
        print("   Remaining tools:", remaining)
    return tools'''

new_func = '''def _fit_schema_to_budget(messages, tools_schema, max_tokens, budget=_LLM_INPUT_TOKEN_BUDGET):
    """Drop the least important tools until prompt+schema fits the provider cap.

    Providers reject an oversized request with 413 and llm_reply then falls
    through to "all providers unavailable", which looks like an outage but is
    really a payload-size problem. Core tools are never dropped; the rest are
    removed largest-first until the estimated token count fits.
    """
    def est(tools):
        payload = json.dumps({"messages": messages, "tools": tools,
                              "max_tokens": max_tokens})
        return len(payload) // 4

    tools = list(tools_schema)
    print(f"🔧 _fit_schema_to_budget: budget={budget}, initial tools={len(tools)}")
    for t in tools:
        print(f"   Tool: {t['function']['name']} (core={t['function']['name'] in _LLM_CORE_TOOLS})")
    if est(tools) <= budget:
        print(f"🔧 _fit_schema_to_budget: under budget, returning {len(tools)} tools")
        return tools
    # NEVER drop file operation tools - they are critical for local work
    file_tools = {t for t in tools if t["function"]["name"] in _FILE_CORE_TOOLS}
    print(f"🔧 _fit_schema_to_budget: file tools={len(file_tools)}")
    for t in file_tools:
        print(f"   File tool: {t['function']['name']}")
    droppable = [t for t in tools
                 if t["function"]["name"] not in _LLM_CORE_TOOLS]
    print(f"🔧 _fit_schema_to_budget: droppable={len(droppable)}, core={len(tools)-len(droppable)}")
    # Biggest schemas cost the most tokens, so shed those first.
    droppable.sort(key=lambda t: len(json.dumps(t)), reverse=True)
    for t in droppable:
        if est(tools) <= budget:
            break
        tools.remove(t)
    # If still over budget, we have a problem - but NEVER drop file tools
    if est(tools) > budget:
        print(f"⚠️ Schema still over budget ({est(tools)} > {budget}) after dropping non-core tools")
        print(f"   Keeping {len(tools)} tools including file tools: {[t['function']['name'] for t in tools if t['function']['name'] in _FILE_CORE_TOOLS]}")
    if len(tools) != len(tools_schema):
        print("✂️ schema trimmed %d -> %d tools to fit %d-token budget (est %d)"
              % (len(tools_schema), len(tools), budget, est(tools)))
        remaining = [t["function"]["name"] for t in tools]
        print("   Remaining tools:", remaining)
    return tools'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open(r'C:\Users\chris\StudentSyncSA\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Function replaced successfully")
else:
    print("OLD FUNCTION NOT FOUND")
    # Try to find it
    idx = content.find('def _fit_schema_to_budget')
    if idx >= 0:
        print("Found at index:", idx)
        print(content[idx:idx+200])