# ace_config.py
# General-purpose configuration loader for the ACEsi framework.
# Loads ace_config.yaml and exposes typed accessors.

import os
import json

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DATA_DIR, "ace_config.yaml")

_config = None


def load():
    """Load and cache the YAML config. Returns the parsed dict."""
    global _config
    if _config is not None:
        return _config
    try:
        import yaml
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: minimal YAML parser for our specific structure
        _config = _parse_simple_yaml(CONFIG_PATH)
    except FileNotFoundError:
        _config = _default_config()
    return _config


def get(key_path, default=None):
    """Dot-notation get: 'global.default_context' -> value."""
    cfg = load()
    parts = key_path.split(".")
    cur = cfg
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def get_global(key, default=None):
    return get(f"global.{key}", default)


def get_context(name=None):
    """Get a context definition. If name is None, returns the active context."""
    if name is None:
        import ace_context as _ctx_mod
        try:
            name = _ctx_mod._active_name
        except Exception:
            name = get_global("default_context", "lipsyncstudent")
    ctxs = load().get("contexts", {})
    return ctxs.get(name)


def all_contexts():
    return list(load().get("contexts", {}).keys())


def _default_config():
    return {
        "global": {"version": "1.0", "default_context": "lipsyncstudent"},
        "contexts": {
            "lipsyncstudent": {"name": "StudentSyncSA", "type": "flutter_android"},
        },
    }


def _parse_simple_yaml(path):
    """Minimal YAML parser for nested dicts/lists with comments.
    Only supports the subset used by ace_config.yaml."""
    result = {}
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            # Strip comments
            stripped = line.rstrip()
            if "#" in stripped:
                idx = stripped.index("#")
                stripped = stripped[:idx]
            stripped = stripped.rstrip()
            if not stripped.strip():
                continue
            lines.append(stripped)

    def parse_value(s):
        s = s.strip()
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        if s.startswith("'") and s.endswith("'"):
            return s[1:-1]
        if s in ("null", "None", "~", ""):
            return None
        if s in ("true", "True"):
            return True
        if s in ("false", "False"):
            return False
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        if s.startswith("[") and s.endswith("]"):
            return [parse_value(x.strip()) for x in s[1:-1].split(",") if x.strip()]
        return s

    # Simple line-by-line indentation parser
    root = {}
    stack = [(-1, root)]
    for line in lines:
        indent = len(line) - len(line.lstrip())
        content = line.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if ":" in content and not content.startswith("-"):
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()
            if val:
                parent[key] = parse_value(val)
            else:
                new_dict = {}
                parent[key] = new_dict
                stack.append((indent, new_dict))
        elif content.startswith("- "):
            item = parse_value(content[2:])
            if isinstance(parent, list):
                parent.append(item)
            else:
                # parent should be a list
                for k in parent:
                    pass
                # This is a list under a key — parent is dict, convert
                pass
    return {"global": {}, "contexts": {}, "_raw": root}
