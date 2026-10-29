import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# Configure logging to BOTH file and stdout so you can see it
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('acesi_debug.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

app = Flask(__name__)

# Print configuration on startup so we know what was actually loaded
log.info("=" * 60)
log.info("ACEsi SERVER STARTING")
log.info(f"OLLAMA_ENDPOINT env: {os.environ.get('OLLAMA_ENDPOINT')!r}")
log.info(f"OLLAMA_MODEL env: {os.environ.get('OLLAMA_MODEL')!r}")
log.info(f"Python: {sys.version}")
log.info(f"Working dir: {os.getcwd()}")
log.info("=" * 60)

# Read from env with fallbacks
OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "tinyllama:latest")
OLLAMA_BASE = OLLAMA_ENDPOINT.rsplit("/api/", 1)[0]  # http://localhost:11434

log.info(f"Using OLLAMA_ENDPOINT = {OLLAMA_ENDPOINT}")
log.info(f"Using OLLAMA_MODEL    = {OLLAMA_MODEL}")
log.info(f"Using OLLAMA_BASE     = {OLLAMA_BASE}")


def verify_ollama():
    """Run at startup to confirm Ollama is reachable from THIS process."""
    log.info("--- Startup Ollama health check ---")
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        log.info(f"GET {OLLAMA_BASE}/api/tags -> {r.status_code}")
        if r.status_code == 200:
            models = [m.get("name") for m in r.json().get("models", [])]
            log.info(f"Models visible to server: {models}")
            if OLLAMA_MODEL not in models:
                log.warning(f"Configured model {OLLAMA_MODEL!r} NOT in model list!")
            else:
                log.info(f"Configured model {OLLAMA_MODEL!r} is present")
            return True
        log.error(f"Ollama health check failed: {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Ollama health check EXCEPTION: {type(e).__name__}: {e}")
        return False


@app.route('/health', methods=['GET'])
def health():
    """Simple endpoint to confirm the server itself is alive."""
    ok = verify_ollama()
    return jsonify({
        "server": "ok",
        "ollama_reachable": ok,
        "endpoint": OLLAMA_ENDPOINT,
        "model": OLLAMA_MODEL,
    })


@app.route('/chat', methods=['POST'])
def chat():
    # === INSTRUMENTATION: log every incoming request ===
    data = request.json
    user_message = data.get('message', '') if data else ''
    log.info(f"[CHAT] Received message: {user_message!r}")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": user_message}],
        "stream": False,
    }
    log.info(f"[CHAT] Forwarding to {OLLAMA_ENDPOINT}")
    log.info(f"[CHAT] Payload: {json.dumps(payload)}")

    try:
        response = requests.post(
            OLLAMA_ENDPOINT,
            json=payload,
            timeout=120,
        )
        log.info(f"[CHAT] Ollama returned status {response.status_code}")
        log.info(f"[CHAT] Ollama raw response: {response.text[:500]}")

        if response.status_code == 200:
            try:
                body = response.json()
            except Exception as e:
                log.error(f"[CHAT] Failed to parse Ollama JSON: {e}")
                return jsonify({"reply": f"Bad JSON from Ollama: {response.text[:200]}"})

            if "message" in body and "content" in body["message"]:
                reply = body["message"]["content"]
                log.info(f"[CHAT] Reply: {reply[:200]}")
                return jsonify({"reply": reply})

            if "error" in body:
                log.error(f"[CHAT] Ollama returned error: {body['error']}")
                return jsonify({"reply": f"Ollama error: {body['error']}"})

            log.error(f"[CHAT] Unexpected response shape: {body}")
            return jsonify({"reply": f"Unexpected response: {body}"})

        return jsonify({"reply": f"Ollama error: HTTP {response.status_code} - {response.text[:200]}"})

    except requests.exceptions.ConnectionError as e:
        log.error(f"[CHAT] ConnectionError: {e}")
        return jsonify({"reply": f"Ollama connection refused. Is Ollama running on {OLLAMA_BASE}?"})
    except requests.exceptions.Timeout as e:
        log.error(f"[CHAT] Timeout: {e}")
        return jsonify({"reply": f"Ollama timed out after 120s"})
    except Exception as e:
        log.error(f"[CHAT] Unexpected exception: {type(e).__name__}: {e}")
        return jsonify({"reply": f"Unexpected error: {type(e).__name__}: {e}"})


# Run health check at import time too
verify_ollama()

if __name__ == '__main__':
    log.info("Starting Flask on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)