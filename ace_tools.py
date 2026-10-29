# ace_tools.py
# General-purpose tool registry with capability-based access control.
#
# Tools self-declare what capabilities they need. A tool is only executable when
# the active Context satisfies those capabilities. This is what makes ACEsi
# general-purpose: a "web_only" context won't have build_apk, and a "code"
# context won't have ui_tap.
#
# Each tool entry: (name, function, arg_keys, capabilities, description, schema)

import os

# ── Capability tags ─────────────────────────────────────────────────────────
#
# A tool declares one or more capability tags. The Context's `tool_caps` setting
# determines which caps are satisfied.
CAP_UI = "ui"            # Android device / UI automation
CAP_CDP = "cdp"          # Chrome DevTools Protocol access
CAP_CODE = "code"        # file system + code editing
CAP_GIT = "git"          # git operations
CAP_BUILD = "build"      # building APKs / compiling
CAP_NET = "net"          # network probing / curl
CAP_CTRL = "ctrl"        # runtime controls (restart, etc.)
CAP_NOTIFY = "notify"    # push notifications

# ── Tool registry ───────────────────────────────────────────────────────────
# Format: name -> (fn, arg_keys, caps, description, schema_dict)
_REGISTRY = {}


def register(name, fn, arg_keys, caps, description, schema=None):
    _REGISTRY[name] = {
        "fn": fn,
        "arg_keys": arg_keys,
        "caps": caps,
        "description": description,
        "schema": schema or {},
    }


def get_tool(name):
    return _REGISTRY.get(name)


def all_tools():
    return list(_REGISTRY.keys())


def tools_for_caps(satisfied_caps):
    """Return tool names whose capabilities are a subset of `satisfied_caps`."""
    result = []
    for name, t in _REGISTRY.items():
        if all(c in satisfied_caps for c in t["caps"]):
            result.append(name)
    return result


def tool_caps(name):
    t = _REGISTRY.get(name)
    return t["caps"] if t else []


def required_args(name):
    t = _REGISTRY.get(name)
    return t["arg_keys"] if t else []


def tool_schema(name):
    """Return OpenAI-style tool schema for a registered tool."""
    t = _REGISTRY.get(name)
    if not t:
        return None
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": t["description"],
            "parameters": t["schema"],
        },
    }


def schema_for(names):
    """Build a TOOLS_SCHEMA list for the given tool names (in order)."""
    return [tool_schema(n) for n in names if get_tool(n)]


def capabilities_satisfied(name, active_caps):
    """Check if all of a tool's capabilities are in the active set."""
    t = _REGISTRY.get(name)
    if not t:
        return False
    return all(c in active_caps for c in t["caps"])
