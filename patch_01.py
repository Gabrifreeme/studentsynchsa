# -*- coding: utf-8 -*-
# patch_01.py (v2) - Chat auth scaffolding for server.py. CRLF-safe.
import io, sys, re

PATH = r"C:\Users\chris\LipSyncStudent\server.py"
MARK_A = "# --- CHAT AUTH BEGIN ---"

with io.open(PATH, "r", encoding="utf-8", newline="") as f:
    src = f.read()

if MARK_A in src:
    print("ABORT: patch_01 already applied (marker found).")
    sys.exit(1)

had_bom = src.startswith("\ufeff")
crlf_before = src.count("\r\n")
lf_only_before = src.count("\n") - crlf_before
print("PRE: bom=%s crlf=%d bare_lf=%d chars=%d" % (had_bom, crlf_before, lf_only_before, len(src)))

EOL = "\r\n"

def to_crlf(block):
    # Normalize whatever we wrote (which is \n) to CRLF for this file.
    return block.replace("\r\n", "\n").replace("\n", EOL)

lines = src.splitlines(keepends=True)

# ---- 1. import anchor: after 'from urllib.parse import quote_plus' ----
assert "from urllib.parse import quote_plus" in lines[22], "L23 import anchor mismatch"
IMPORTS_BLOCK = to_crlf(
    "import secrets\n"
    "import hashlib as _chat_hashlib\n"
    "import functools\n"
    "from flask import g\n"
    "from flask_socketio import emit as _sio_emit, join_room as _sio_join, leave_room as _sio_leave, disconnect as _sio_disconnect\n"
)
lines.insert(23, IMPORTS_BLOCK)

src2 = "".join(lines)

# ---- 2. extend init_db() just before its conn.commit() ----
init_idx = src2.find("def init_db():")
assert init_idx != -1, "init_db() not found"
commit_idx = src2.find("conn.commit()", init_idx)
assert commit_idx != -1, "init_db conn.commit() not found"
init_call_idx = src2.find("\r\ninit_db()\r\n", init_idx)
if init_call_idx == -1:
    init_call_idx = src2.find("\ninit_db()\n", init_idx)
assert init_call_idx != -1, "module-level init_db() call not found"
assert commit_idx < init_call_idx, "commit sanity failed"

CHAT_TABLES = to_crlf(
    "    # Chat Phase 2 tables (cross-device chat)\n"
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_users (user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, last_seen TEXT)')\n"
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_rooms (room_id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, created_at TEXT NOT NULL)')\n"
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT NOT NULL, user_id TEXT NOT NULL, display_name TEXT NOT NULL, body TEXT NOT NULL, attachment_json TEXT, created_at TEXT NOT NULL)')\n"
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_reads (room_id TEXT NOT NULL, user_id TEXT NOT NULL, last_read_id INTEGER NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (room_id, user_id))')\n"
    "    c.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_room_created ON chat_messages(room_id, created_at)')\n"
    "    c.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id)')\n"
)
src2 = src2[:commit_idx] + CHAT_TABLES + src2[commit_idx:]

# ---- 3. helper block after module-level init_db() call ----
m = re.search(r'(?:\r\n|\n)init_db\(\)(?:\r\n|\n)', src2)
assert m is not None, "init_db() module-level call anchor missing (regex)"
anchor_idx = m.end()

HELPER_RAW = r'''
# --- CHAT AUTH BEGIN ---
# Token-based identity for cross-device chat + gated routes.
# Loopback (127.0.0.1 / ::1 / localhost) always passes -- preserves local dev UX.
# Raw tokens are never stored; only sha256 hashes in chat_users.token_hash.
def _is_loopback(addr):
    if not addr:
        return False
    return addr in ("127.0.0.1", "::1", "localhost") or addr.startswith("127.")

def _chat_hash(tok):
    return _chat_hashlib.sha256(tok.encode("utf-8")).hexdigest()

def _now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def _chat_conn():
    conn = sqlite3.connect("ace_memory.db")
    conn.row_factory = sqlite3.Row
    return conn

def _issue_token(display_name):
    display_name = (display_name or "").strip()
    if not display_name or len(display_name) > 64:
        return None, "display_name required (1-64 chars)"
    user_id = uuid.uuid4().hex
    raw_tok = secrets.token_urlsafe(32)
    th = _chat_hash(raw_tok)
    now = _now_iso()
    conn = _chat_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM chat_users WHERE display_name=?", (display_name,))
        if cur.fetchone():
            return None, "display_name already registered; revoke first or pick another"
        cur.execute(
            "INSERT INTO chat_users (user_id, display_name, token_hash, created_at, last_seen) VALUES (?,?,?,?,?)",
            (user_id, display_name, th, now, now),
        )
        conn.commit()
    except Exception as e:
        try: conn.rollback()
        except Exception: pass
        return None, "issue failed: %s" % e
    finally:
        conn.close()
    return {"user_id": user_id, "display_name": display_name, "token": raw_tok}, None

def _lookup_token(raw_tok):
    if not raw_tok:
        return None
    th = _chat_hash(raw_tok)
    conn = _chat_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, display_name FROM chat_users WHERE token_hash=?", (th,))
        row = cur.fetchone()
        if not row:
            return None
        cur.execute("UPDATE chat_users SET last_seen=? WHERE user_id=?", (_now_iso(), row["user_id"]))
        conn.commit()
        return {"user_id": row["user_id"], "display_name": row["display_name"]}
    finally:
        conn.close()

def _extract_token(req):
    tok = req.headers.get("X-ACEsi-Token")
    if tok:
        return tok.strip()
    auth = req.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None

def require_token(fn):
    @functools.wraps(fn)
    def _wrap(*args, **kwargs):
        if _is_loopback(request.remote_addr):
            g.chat_user = {"user_id": "loopback", "display_name": "loopback"}
            return fn(*args, **kwargs)
        ident = _lookup_token(_extract_token(request))
        if not ident:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        g.chat_user = ident
        return fn(*args, **kwargs)
    return _wrap

@app.route("/api/auth/issue", methods=["POST", "OPTIONS"])
def api_auth_issue():
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(silent=True) or {}
    payload, err = _issue_token(data.get("display_name"))
    if err:
        return jsonify({"ok": False, "error": err}), 400
    return jsonify({"ok": True, **payload})

@app.route("/api/auth/revoke", methods=["POST"])
def api_auth_revoke():
    if not _is_loopback(request.remote_addr):
        return jsonify({"ok": False, "error": "loopback only"}), 403
    data = request.get_json(silent=True) or {}
    uid = (data.get("user_id") or "").strip()
    if not uid:
        return jsonify({"ok": False, "error": "user_id required"}), 400
    conn = _chat_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_users WHERE user_id=?", (uid,))
        n = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True, "deleted": n})

def _chat_boot_report():
    try:
        conn = _chat_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM chat_users"); u = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM chat_rooms"); r = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM chat_messages"); m = cur.fetchone()["n"]
        conn.close()
        print("[chat] init ok users=%d rooms=%d messages=%d" % (u, r, m))
    except Exception as e:
        print("[chat] init report failed: %s" % e)

_chat_boot_report()
# --- CHAT AUTH END ---
'''
HELPER = to_crlf(HELPER_RAW)

src2 = src2[:anchor_idx] + HELPER + src2[anchor_idx:]

# ---- 4. write back ----
with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(src2)

crlf_after = src2.count("\r\n")
lf_only_after = src2.count("\n") - crlf_after
print("POST: crlf=%d bare_lf=%d chars=%d" % (crlf_after, lf_only_after, len(src2)))
print("DONE patch_01")
