# -*- coding: utf-8 -*-
# patch_01_repair.py - fix the 8-space comment + unindented conn.commit() damage
# from patch_01's splice. Asserts current broken shape, then repairs, then compiles.
import io, sys, subprocess

PATH = r"C:\Users\chris\LipSyncStudent\server.py"
EOL = "\r\n"

with io.open(PATH, "r", encoding="utf-8", newline="") as f:
    src = f.read()

lines = src.splitlines(keepends=True)

# Locate the broken comment line (my marker, 8 spaces) and the unindented conn.commit()
# We expect them at a small distance; find them by content within 20 lines of each other.
def find_line_index(predicate, start=0):
    for i in range(start, len(lines)):
        if predicate(lines[i].rstrip("\r\n")):
            return i
    return -1

def strip_eol(s): return s.rstrip("\r\n")

idx_comment = find_line_index(lambda l: l == "        # Chat Phase 2 tables (cross-device chat)")
assert idx_comment != -1, "8-space chat comment not found"
idx_commit = find_line_index(lambda l: l == "conn.commit()", idx_comment)
assert idx_commit != -1, "unindented conn.commit() not found after comment"
assert idx_commit - idx_comment <= 12, "commit too far from comment; wrong match"

# Sanity: the 6 CREATE lines between must all start with 4 spaces
for k in range(idx_comment + 1, idx_commit):
    t = strip_eol(lines[k])
    assert t.startswith("    c.execute("), "unexpected line at %d: %r" % (k+1, t)

# Build the clean replacement block for lines [idx_comment .. idx_commit] inclusive.
REPLACEMENT = [
    "    # Chat Phase 2 tables (cross-device chat)" + EOL,
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_users (user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, last_seen TEXT)')" + EOL,
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_rooms (room_id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, created_at TEXT NOT NULL)')" + EOL,
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT NOT NULL, user_id TEXT NOT NULL, display_name TEXT NOT NULL, body TEXT NOT NULL, attachment_json TEXT, created_at TEXT NOT NULL)')" + EOL,
    "    c.execute('CREATE TABLE IF NOT EXISTS chat_reads (room_id TEXT NOT NULL, user_id TEXT NOT NULL, last_read_id INTEGER NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (room_id, user_id))')" + EOL,
    "    c.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_room_created ON chat_messages(room_id, created_at)')" + EOL,
    "    c.execute('CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id)')" + EOL,
    "    conn.commit()" + EOL,
]

new_lines = lines[:idx_comment] + REPLACEMENT + lines[idx_commit + 1:]
out = "".join(new_lines)

with io.open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(out)

print("REPAIRED lines %d-%d" % (idx_comment + 1, idx_commit + 1))

# Verify compile in-process
r = subprocess.run([sys.executable, "-m", "py_compile", PATH], capture_output=True, text=True)
if r.returncode == 0:
    print("COMPILE OK")
else:
    print("COMPILE FAIL")
    print(r.stdout)
    print(r.stderr)
    sys.exit(1)
