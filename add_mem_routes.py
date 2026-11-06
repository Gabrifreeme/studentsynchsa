#!/usr/bin/env python3
import re

server_path = r'C:\Users\chris\LipSyncStudent\server.py'

with open(server_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the api_settings_post function and add memory routes after it
# The POST route handler ends and we need to insert after it

# Strategy: find the end of api_settings_post by looking for the next @app.route or major section
search_pattern = '''@app.route("/api/settings", methods=["POST"])
def api_settings_post():'''

idx = content.find(search_pattern)
if idx < 0:
    # Try alternative pattern
    search_pattern = '@app.route("/api/settings", methods=["POST"])'
    idx = content.find(search_pattern)
    if idx < 0:
        print('ERROR: Could not find /api/settings route')
        exit(1)

print(f'Found /api/settings at index {idx}')

# Now find where this function ends - look for the next @app.route or major section
# Look for the pattern that marks the end of settings routes
end_pattern = '''except Exception as e:
    pass

@app.route("/api/live_logs"'''

end_idx = content.find(end_pattern, idx)
if end_idx < 0:
    # Try another pattern
    end_pattern2 = '''except Exception as e:'''
    end_idx = content.find(end_pattern2, idx)
    
if end_idx < 0:
    print('ERROR: Could not find end of api_settings_post')
    # Just show what's after the search position
    print(content[idx:idx+200])
    exit(1)

print(f'Found end of settings post at {end_idx}')

# The memory routes to insert
memory_routes ='''

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
'''

# Insert the memory routes before the end marker
new_content = content[:end_idx] + memory_routes + content[end_idx:]

with open(server_path, 'w', encoding='utf-8', errors='replace') as f:
    f.write(new_content)

print('SUCCESS: Memory routes added to server.py')