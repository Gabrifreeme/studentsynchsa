"""Legacy /api/autofix route - NOT registered by server.py.

The live endpoint is `autofix()` in server.py. This module is kept for
reference only. It used to carry a hardcoded Groq key, which is exactly the
kind of thing that ends up in git history; the key now comes from the
environment, and the file fails loudly if it is missing rather than silently
shipping a secret.

Set the key in the gitignored .env:

    GROQ_API_KEY=gsk_...
"""

import os

import requests
from flask import jsonify, request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
PROMPT = (
    "You are a code syntax fixer. Fix ONLY syntax errors in the code below. "
    "Return ONLY the complete corrected code, with no explanations.\n\n"
    "CODE:\n"
)


def _groq_key():
    """Read the Groq key at call time so a restart is not needed after .env edits."""
    return os.environ.get("GROQ_API_KEY", "").strip()


def _strip_fence(text):
    """Drop a leading ```lang line and the closing fence, if the model added one."""
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def register_autofix(app):
    @app.route("/api/autofix", methods=["POST", "OPTIONS"])
    def api_autofix():
        if request.method == "OPTIONS":
            return ("", 204)

        data = request.get_json(silent=True) or {}
        code = data.get("code", "")
        if len(code) > 8000:
            code = code[:8000] + "\n\n... [trimmed for token limit]"
        if not code.strip():
            return jsonify(ok=False, error="No code provided"), 400

        prompt = PROMPT + code

        key = _groq_key()
        if key:
            try:
                r = requests.post(
                    GROQ_URL,
                    headers={
                        "Authorization": "Bearer %s" % key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "openai/gpt-oss-20b",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0,
                    },
                    timeout=60,
                )
                if r.status_code == 200:
                    fixed = _strip_fence(
                        r.json()["choices"][0]["message"]["content"]
                    )
                    if fixed:
                        return jsonify(ok=True, fixed_code=fixed)
                else:
                    # Name the status only: the body can echo request details
                    # and this used to be printed in full.
                    print("Autofix: Groq HTTP %d" % r.status_code)
            except Exception as e:
                print("Autofix: Groq failed: %s: %s" % (type(e).__name__, e))

        # Local fallback so the endpoint still works offline / without a key.
        try:
            r2 = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "qwen2.5-coder:7b",
                    "prompt": "Fix ONLY syntax errors. Return corrected code only.\n\nCODE:\n" + code,
                    "stream": False,
                    "options": {"temperature": 0},
                },
                timeout=110,
            )
            fixed = _strip_fence(r2.json().get("response", ""))
            if fixed:
                return jsonify(ok=True, fixed_code=fixed)
        except Exception as e2:
            print("Autofix: Ollama fallback failed: %s: %s" % (type(e2).__name__, e2))

        return jsonify(ok=False, error="No model could fix the code"), 200
