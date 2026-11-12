import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    py = f.read()

# 1. Inject the stdout interceptor right after imports
hook_code = """
# --- ROUTE STDOUT TO ACEsi TERMINAL ---
import sys
import threading
from io import StringIO

class TerminalLogger(StringIO):
    def write(self, msg):
        if msg.strip():
            try:
                socketio.emit('terminal_output', '\\r\\n\\x1b[33m[SERVER] ' + msg.replace('\\n', '\\r\\n') + '\\x1b[0m')
            except Exception:
                pass
        return super().write(msg)

# Only redirect if we haven't already
if not hasattr(sys.stdout, '_acesi_hooked'):
    original_stdout = sys.stdout
    logger = TerminalLogger()
    logger._acesi_hooked = True
    sys.stdout = logger
# -------------------------------------
"""

# Insert after the last import (before app = Flask)
if "TerminalLogger" not in py:
    # Find the app = Flask line
    insert_idx = py.find("app = Flask(")
    assert insert_idx != -1, "Could not find app = Flask"
    py = py[:insert_idx] + hook_code + "\n" + py[insert_idx:]
    print("BACKEND: Injected stdout-to-socket hook")
else:
    print("BACKEND: Hook already present")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(py)
print("PATCH COMPLETE")
