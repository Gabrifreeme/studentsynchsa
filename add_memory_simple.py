#!/usr/bin/env python3
import sys

server_path = r'C:\Users\chris\LipSyncStudent\server.py'

with open(server_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the ping route
search_str = '@app.route("/api/ping", methods=["POST"])'
idx = content.find(search_str)

if idx > 0:
    # Find the "# ACEsi System Settings" comment
    settings_marker = content.find('# ACEsi System Settings')
    if settings_marker > 0:
        memory_routes = '''

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
        addOutput("Memory saved to file")
        return jsonify({"status": "saved", "memory": memory_text})
    except Exception as e:
        print(f"[memory] save failed: {e}")
        return jsonify({"status": "error", "message": str(e)})

# ACEsi System Settings'''
        content = content[:settings_marker] + memory_routes + content[settings_marker:]
        with open(server_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(content)
        print('SUCCESS: Added memory routes')
    else:
        print('ERROR: Could not find "# ACEsi System Settings" marker')
else:
    print('ERROR: Could not find ping route')