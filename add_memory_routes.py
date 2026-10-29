with open(r'C:\Users\chris\LipSyncStudent\server.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Add memory routes after the ping route
old_ping_end = '@app.route("/api/ping", methods=["POST"])\ndef api_ping():\n    # TODO: Trigger notify tool / send test ping\n    addOutput("📡 Send Ping triggered")\n    return jsonify({"status": "ping sent"})\n\n\n# ── ACEsi System Settings ──────────────────────────────────────────────'

new_ping_end = '''@app.route("/api/ping", methods=["POST"])
def api_ping():
    # TODO: Trigger notify tool / send test ping
    addOutput("📡 Send Ping triggered")
    return jsonify({"status": "ping sent"})


@app.route("/api/memory", methods=["GET"])
def api_memory_get():
    try:
        memory_path = _SETTINGS_PATH.replace("config.json", "memory.txt")
        try:
            with open(memory_path, "r", encoding="utf-8") as f:
                memory = f.read()
        except Exception:
            memory = ""
        return jsonify({"memory": memory})
    except Exception as e:
        return jsonify({"memory": "", "error": str(e)})


@app.route("/api/memory", methods=["POST"])
def api_memory_post():
    data = request.get_json(silent=True) or {}
    memory_text = data.get("memory", "")
    try:
        memory_path = _SETTINGS_PATH.replace("config.json", "memory.txt")
        with open(memory_path, "w", encoding="utf-8") as f:
            f.write(memory_text)
        addOutput("💾 Memory saved to file")
        return jsonify({"status": "saved", "memory": memory_text})
    except Exception as e:
        print(f"[memory] save failed: {e}")
        return jsonify({"status": "error", "message": str(e)})


# ── ACEsi System Settings ──────────────────────────────────────────────'''

if old_ping_end in content:
    content = content.replace(old_ping_end, new_ping_end)
    with open(r'C:\Users\chris\LipSyncStudent\server.py', 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    print('Added memory routes successfully')
else:
    print('Could not find pattern to replace')
    # Show the actual end of file
    idx = content.find('@app.route("/api/ping"')
    if idx > 0:
        print('Found ping route at index', idx)
        print(content[idx:idx+400])