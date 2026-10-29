from flask import request, jsonify
import requests

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

        prompt = (
            "You are a code syntax fixer. Fix ONLY syntax errors in the code below. "
            "Return ONLY the complete corrected code, with no explanations.\n\n"
            "CODE:\n" + code
        )

        try:
            GROQ_API_KEY = "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"
            
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "openai/gpt-oss-20b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0
            }
            
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            print("Groq response:", r.json())
            
            if r.status_code != 200:
                return jsonify(ok=False, error=f"Groq Error: {r.text}"), r.status_code

            fixed = r.json()["choices"][0]["message"]["content"].strip()
            
            if fixed.startswith("```"):
                fixed = "\n".join(fixed.split("\n")[1:-1])
                
            return jsonify(ok=True, fixed_code=fixed)
            
        except Exception as e:
            print("Autofix exception:", e)
            # Fallback to Ollama
            try:
                r2 = requests.post("http://127.0.0.1:11434/api/generate", json={"model":"qwen2.5-coder:7b","prompt":"Fix ONLY syntax errors. Return corrected code only.\n\nCODE:\n"+code,"stream":False,"options":{"temperature":0}}, timeout=110)
                print("Ollama fallback response:", r2.json())
                fixed = r2.json().get("response","").strip()
                if fixed:
                    return jsonify(ok=True, fixed_code=fixed)
            except Exception as e2:
                print("Ollama fallback failed:", e2)
            return jsonify(ok=False, error=str(e)), 500