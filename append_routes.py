with open('C:\\Users\\chris\\LipSyncStudent\\server.py','a',encoding='utf-8') as f:
    f.write('''

# ===== Explorer file routes =====
@app.route("/api/files", methods=["GET"])
def api_files():
    import os
    files = []
    lib_dir = "lib"
    if os.path.isdir(lib_dir):
        for root, dirs, filenames in os.walk(lib_dir):
            for filename in filenames:
                full = os.path.join(root, filename)
                rel = os.path.relpath(full, lib_dir)
                files.append(rel)
    return jsonify({"files": sorted(files)})

@app.route("/api/file-content", methods=["GET"])
def api_file_content():
    path = (request.args.get("path") or "").strip()
    if not path or ".." in path:
        return jsonify({"ok": False, "error": "bad path"}), 400
    full = os.path.join("lib", path)
    try:
        with open(full, "r", encoding="utf-8") as fh:
            return jsonify({"ok": True, "content": fh.read()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 404
''')
print('routes appended')
