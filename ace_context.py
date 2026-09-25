# ace_context.py
# Context manager for ACEsi's general-purpose autonomous agent framework.
#
# A "context" is a configuration environment that defines:
# - which Android app / device to talk to (app_package, cdp_url_fragment)
# - which LLM profile to use (cloud, local, code, etc.)
# - which tools are permitted (capability restrictions)
# - what prompt overlay to inject (known app structure, shortcuts)
# - default startup URL, project root, etc.
#
# The active context is selected per-request via the `context` parameter,
# or defaults to the global default_context. Contexts load from ace_config.yaml.

import os
import sys
import yaml
import threading

_lock = threading.RLock()
_CONFIG = None
_ACTIVE_CONTEXT_NAME = None


def _config_path():
    """Return the path to ace_config.yaml, searching project root first."""
    for d in ("C:\\Users\\chris\\StudentSyncSA", os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        p = os.path.join(d, "ace_config.yaml")
        if os.path.exists(p):
            return p
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ace_config.yaml")


def _load():
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    path = _config_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            data = {}
    except Exception as e:
        sys.stderr.write(f"[ace_context] WARNING: could not load {path}: {e}\n")
        data = {}
    data.setdefault("global", {})
    data.setdefault("contexts", {})
    data.setdefault("profiles", {})
    data.setdefault("tool_caps", {})
    _CONFIG = data
    return _CONFIG


def _reset():
    """Clear cached config (used in tests / hot reload)."""
    global _CONFIG
    _CONFIG = None


def list_contexts():
    """Return a list of context names defined in config."""
    data = _load()
    return list((data.get("contexts") or {}).keys())


def get_context(name=None):
    """Return the config dict for a named context, merged with global defaults.

    Returns None if the context doesn't exist.
    """
    data = _load()
    name = name or _ACTIVE_CONTEXT_NAME or data.get("global", {}).get("default_context")
    if not name:
        return None
    ctxs = data.get("contexts") or {}
    if name not in ctxs:
        # Fall back to "generic" if it exists, else first context
        if "generic" in ctxs:
            name = "generic"
        else:
            names = list(ctxs.keys())
            if not names:
                return None
            name = names[0]
    ctx = dict(ctxs[name])
    ctx["_name"] = name
    ctx.setdefault("app_package", None)
    ctx.setdefault("project_root", None)
    ctx.setdefault("startup_url", None)
    ctx.setdefault("cdp_url_fragment", None)
    ctx.setdefault("known_structure", None)
    ctx.setdefault("prompt_overlay", None)
    ctx.setdefault("shortcuts", {})
    ctx.setdefault("llm_profile", "local")
    ctx.setdefault("tool_caps", None)
    ctx.setdefault("type", "generic")
    return ctx


def get_active_context():
    """Return the currently active context dict, or the default."""
    return get_context(_ACTIVE_CONTEXT_NAME)


def set_active_context(name):
    """Switch the active context. Returns True on success."""
    global _ACTIVE_CONTEXT_NAME
    ctxs = _load().get("contexts") or {}
    if name in ctxs:
        with _lock:
            _ACTIVE_CONTEXT_NAME = name
        return True
    return False


def get_profile(name):
    """Return the LLM provider chain for a named profile."""
    data = _load()
    return data.get("profiles", {}).get(name, [])


def get_tool_caps(tool_caps_name):
    """Return the allowed tool names for a named tool-cap group."""
    data = _load()
    caps = data.get("tool_caps", {})
    if tool_caps_name in caps:
        return caps[tool_caps_name].get("tools", [])
    if str(tool_caps_name).lower() == "all":
        return None
    return []


def resolve_llm_profile(context):
    """Given a context dict, return the LLM provider chain to try."""
    return get_profile(context.get("llm_profile", "local"))


def active_context_name():
    return _ACTIVE_CONTEXT_NAME


def get_active_context_name():
    """Alias for active_context_name (for API ergonomics)."""
    return _ACTIVE_CONTEXT_NAME


class Context:
    """A convenience handle wrapping a context dict."""
    def __init__(self, name=None):
        self._name = name or _ACTIVE_CONTEXT_NAME
        self._ctx = get_context(self._name)

    @property
    def name(self):
        return self._name

    def __getitem__(self, key):
        return self._ctx.get(key) if self._ctx else None

    def get(self, key, default=None):
        return self._ctx.get(key, default) if self._ctx else default

    @property
    def valid(self):
        return self._ctx is not None

    def as_dict(self):
        return dict(self._ctx) if self._ctx else {}


if __name__ == "__main__":
    import json
    print("Contexts:", json.dumps(list_contexts(), indent=2))
    for n in list_contexts():
        print(f"\n--- {n} ---")
        print(json.dumps(get_context(n), indent=2))
