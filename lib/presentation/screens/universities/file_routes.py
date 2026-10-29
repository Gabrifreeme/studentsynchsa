from flask import request, jsonify, send_from_directory
import os

def register_file_routes(app):
    # Point to the lib folder
    LIB_DIR = os.path.join(os.path.dirname(__file__), 'lib')

    @app.route('/api/files', methods=['GET'])
    def list_files():
        try:
            files = []
            for root, dirs, filenames in os.walk(LIB_DIR):
                for f in filenames:
                    if f.endswith('.dart'):
                        # Get path relative to LipSyncStudent folder
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
            
        # Ensure the path is safe and inside lib
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
        data = request.json
        path = data.get('path')
        code = data.get('code')
        
        if not path or code is None:
            return jsonify({"error": "Missing path or code"}), 400

        full_path = os.path.join(os.path.dirname(__file__), path)
        if not full_path.startswith(LIB_DIR):
            return jsonify({"error": "Invalid path"}), 403

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)
            return jsonify({"success": True}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500