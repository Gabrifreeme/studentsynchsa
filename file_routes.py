from flask import request, jsonify
import os

def register_file_routes(app):
    LIB_DIR = os.path.join(os.path.dirname(__file__), 'lib')

    @app.route('/api/files', methods=['GET'])
    def list_files():
        try:
            files = []
            for root, dirs, filenames in os.walk(LIB_DIR):
                for f in filenames:
                    if f.endswith('.dart'):
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, os.path.dirname(__file__))
                        files.append(rel_path.replace('\\', '/'))
            print(f"✅ Explorer API: Found {len(files)} files")
            return jsonify(files)
        except Exception as e:
            print(f"❌ Explorer Error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/file-content', methods=['GET'])
    def get_file_content():
        path = request.args.get('path')
        if not path:
            return jsonify({"error": "No path provided"}), 400
        full_path = os.path.join(os.path.dirname(__file__), path)
        if not full_path.startswith(LIB_DIR):
            return jsonify({"error": "Invalid path"}), 403
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read(), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/save-file', methods=['POST'])
    def save_file_content():
        # ACEsi.html sends data as application/x-www-form-urlencoded
        if request.content_type == 'application/x-www-form-urlencoded':
            filename = request.form.get('filename')
            code = request.form.get('content')
        else:
            data = request.json or {}
            filename = data.get('path')
            code = data.get('code')

        if not filename or code is None:
            return jsonify({"error": "Missing filename or content"}), 400
        
        # Resolve path relative to the app directory
        full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
        
        try:
            # Use a temporary file and replace to handle Windows file locks more robustly
            tmp_path = full_path + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write(code)
            os.replace(tmp_path, full_path)
            return jsonify({"ok": True, "message": f"Successfully saved {filename}"}), 200
        except PermissionError as e:
            return jsonify({"error": f"Permission denied/File locked: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
