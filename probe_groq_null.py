"""Does Groq accept a JSON-Schema type union (string|null) for an optional arg?

If it does, the reduced schema can declare optional strings as nullable and a
model that emits null stops killing the whole round with
"parameters for tool X did not match schema: expected string, but got null".
"""
import json

import requests

import server as S

TOOL = {
    "type": "function",
    "function": {
        "name": "probe_tool",
        "description": "probe",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": ["string", "null"], "description": "optional text"},
                "b": {"type": ["number", "null"], "description": "optional number"},
            },
            "required": [],
        },
    },
}

body = {
    "model": S.GROQ_MODEL,
    "messages": [{"role": "user", "content": "call probe_tool with a=null b=null, nothing else"}],
    "tools": [TOOL],
    "tool_choice": "required",
    "max_tokens": 60,
    "temperature": 0,
}
r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                  headers={"Authorization": "Bearer %s" % S.GROQ_API_KEY,
                           "Content-Type": "application/json"},
                  json=body, timeout=40)
print("HTTP", r.status_code)
if r.status_code == 200:
    msg = r.json()["choices"][0]["message"]
    print("tool_calls:", json.dumps(msg.get("tool_calls"), indent=1)[:600])
else:
    print(r.text[:500])
