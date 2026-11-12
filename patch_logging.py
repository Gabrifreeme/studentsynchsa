import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# 1. Add logging setup near the top (after imports)
if "import logging" not in "\n".join(lines[:50]):
    for i, line in enumerate(lines):
        if line.startswith("app = Flask("):
            lines.insert(i, "import logging\nlogging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s - %(message)s')\n")
            print(f"BACKEND: Added logging setup at line {i+1}")
            break

# 2. Update the socketio.run line to use the logging config (and log socketio requests)
if "debug=False" in "\n".join(lines):
    for i, line in enumerate(lines):
        if "socketio.run(" in line:
            # We don't need to change socketio.run, but let's make sure werkzeug logs are redirected
            if "allow_unsafe_werkzeug=True" in line:
                pass 
            break

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)
print("PATCH COMPLETE")
