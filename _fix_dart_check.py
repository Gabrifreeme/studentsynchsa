p = r'C:\Users\chris\LipSyncStudent\server.py'
src = open(p, 'r', encoding='utf-8').read()

old_code = """        if ext == '.py':
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', tmp_path],
                capture_output=True, text=True, timeout=15
            )
        else:
            result = subprocess.run(
                ['dart', 'analyze', tmp_path],
                capture_output=True, text=True, timeout=30
            )"""

new_code = """        if ext == '.py':
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', tmp_path],
                capture_output=True, text=True, timeout=15
            )
        else:
            # Skip Dart standalone check to avoid false positives without pubspec context
            return jsonify({'ok': True, 'skipped': True, 'message': 'Dart syntax check skipped'})"""

if old_code in src:
    src = src.replace(old_code, new_code)
    open(p, 'w', encoding='utf-8').write(src)
    print("DART SYNTAX CHECK DISABLED")
else:
    print("CODE NOT FOUND")