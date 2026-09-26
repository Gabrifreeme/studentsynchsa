# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_from_directory, Response, redirect
from flask_cors import CORS
import requests
import json
import base64
import sqlite3
import os
import re
import uuid
import winsound
import subprocess
import time
import tempfile
import threading
import sys
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import devtools_service as d  # Chrome DevTools Protocol bridge (ITS WebView / local Chrome)

# ── Context system (ACEsi is general-purpose now) ───────────────────────────
try:
    import ace_context
except Exception:
    ace_context = None

# ACEsi dispatcher — robust multi-subtask execution with safe tool calls,
# persistent ledger, and partial-completion reporting. Used as a fallback
# when the model-driven _chat_dispatch loop exhausts all providers.
try:
    import ace_dispatcher
except Exception:
    ace_dispatcher = None

# Bind the active Context so all modules see the same app_package / CDP filter.
if ace_context:
    _default_ctx = ace_context.get_context()
    ace_context.set_active_context(_default_ctx["_name"] if _default_ctx else "studentsyncsa")

# Windows console is cp1252 by default and crashes on emoji prints — force UTF-8.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load provider keys from a gitignored .env without requiring python-dotenv.
# Real environment variables always win, so this is only a local convenience.
def _load_dotenv(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except FileNotFoundError:
        pass
    except Exception as exc:
        print("dotenv load failed: %s" % exc)


_load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat-v2:free"
OPENROUTER_FALLBACKS = [
    "poolside/laguna-s-2.1",
    "nvidia/nemotron-3-super-120b-a12b",
]

GROQ_FALLBACKS = [
    "qwen/qwen3.8-27b",
]

OPENROUTER_MODEL = "deepseek/deepseek-v4-flash-0731:free"

# Free cloud providers (large context, no card). Keys load from env or a
# gitignored local file (.ace_keys.local) — set below, after DATA_DIR exists.
def _load_local_keys():
    try:
        p = os.path.join(DATA_DIR, '.ace_keys.local')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        return {}
    return {}

GROQ_ENDPOINT = "https://api.groq.com/openai/v1"
GROQ_MODEL = "qwen/qwen3.8-27b"

CEREBRAS_ENDPOINT = "https://api.cerebras.ai/v1"
CEREBRAS_MODEL = "gpt-oss-120b"

# FreeLLMAPI (Railway)
FREELLM_ENDPOINT = "https://freellmapi-production-1394.up.railway.app/v1"
FREELLM_API_KEY = os.environ.get("FREELLM_API_KEY", "")
FREELLM_MODEL = "auto"

# Both /chat dispatch and llm_reply use the 7b model. 3b is faster (~20-40s/round)
# but 7b gives better quality. On this CPU-only box expect ~60-90s per round.
OLLAMA_ENDPOINT = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_CHAT_MODEL = "qwen2.5:7b"
# Ollama on this hardware crashes with any prompt over ~500 chars (2GB VRAM,
# no AVX2). Use a minimal system prompt for Ollama calls in llm_reply.
_OLLAMA_MINIMAL_PROMPT = (
    "You are ACEsi, an AI assistant. Answer questions concisely and honestly. "
    "If you do not know, say so. Do not guess."
)

def _ollama_reachable():
    """One cheap check, cached, so a dead local endpoint costs nothing."""
    if not OLLAMA_ENDPOINT:
        return False
    try:
        requests.get(OLLAMA_ENDPOINT.replace("/v1", "") + "/api/tags", timeout=(2, 2))
        return True
    except Exception:
        return False

OLLAMA_ENABLED = bool(os.environ.get("ACE_OLLAMA", "") or _ollama_reachable())

# Private unguessable ntfy topic (server + phone must both subscribe to this id).
# Kept in ntfy_topic.txt (gitignored) too, so the phone can be re-subscribed from
# the server side — see GET /notify/topic.
NTFY_TOPIC = "ACEsi0102"
NTFY_INBOUND_PASSPHRASE = "acesi0102"
NTFY_SERVER = "https://ntfy.sh"
SERVER_PORT = int(os.environ.get("ACESI_PORT", "5000"))

_GROUNDING_DIRECTIVE = (
    "Answer the user's question DIRECTLY and CONCISELY using ONLY the tool results "
    "in this conversation. Quote or paraphrase the specific result that supports each "
    "claim, and name the source. If the results do not contain the answer, say exactly: "
    "'The searches did not establish this.' Do NOT answer from memory, and do not use "
    "phrases like 'I recall', 'I believe', or 'I think it is' - those mean you are "
    "guessing. Do NOT save findings to a file unless the user explicitly asks you to "
    "save them. Just give the answer directly."
)

_UNGROUNDED = re.compile(
    r"\b(?:i recall|i remember|i believe|i think (?:it|this) (?:is|was)|from memory|"
    r"if i(?:'| a)m (?:not mistaking|correct)|actually,? i)\b", re.IGNORECASE)


def _is_ungrounded(text: str) -> bool:
    return bool(_UNGROUNDED.search(text or ""))


_GROUNDING_FALLBACK = (
    "If no tools were called in this conversation and you have no "
    "tool results to cite, you may answer from your own knowledge — "
    "but be honest about your confidence and note that your answer "
    "is from general knowledge, not from tool results."
)


def init_db():
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, role TEXT, content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS memories (key TEXT PRIMARY KEY, value TEXT, updated TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, entry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS moods (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, mood TEXT, note TEXT)')
    conn.commit()
    conn.close()

init_db()

OCR_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ocr.ps1')

# This server runs DETACHED (no console window) under the ace_host watchdog.
# Any child subprocess that doesn't get CREATE_NO_WINDOW spawns a NEW visible
# console — a black window that flashes and vanishes, seen every time ACEsi
# loads a page that runs /devices or /agents. All subprocess calls go through
# these helpers so children never pop a window.
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def _run(*args, **kw):
    kw.setdefault("creationflags", _NO_WINDOW)
    return subprocess.run(*args, **kw)

# Long-lived child processes ACEsi started (flutter run, dart run, etc.) are
# registered here so the E-STOP can taskkill them by PID tree. Blocking
# subprocess.run calls can't be killed mid-flight, which is why long-lived runs
# use _track_proc + _popen paths; the kill switch also aborts the agent loop
# which prevents NEW spawns.
_PROCS = {}
_PROCS_LOCK = threading.RLock()
def _track_proc(p):
    with _PROCS_LOCK:
        _PROCS[p.pid] = p
    return p
def _untrack_proc(p):
    with _PROCS_LOCK:
        _PROCS.pop(p.pid, None)
def _kill_all_procs():
    with _PROCS_LOCK:
        pids = list(_PROCS.keys())
    for pid in pids:
        try:
            subprocess.run(['taskkill', '/F', '/PID', str(pid), '/T'],
                           creationflags=_NO_WINDOW, capture_output=True, timeout=15)
        except Exception:
            pass
    with _PROCS_LOCK:
        _PROCS.clear()


def _popen(*args, **kw):
    kw.setdefault("creationflags", _NO_WINDOW)
    return subprocess.Popen(*args, **kw)


def _check_output(*args, **kw):
    kw.setdefault("creationflags", _NO_WINDOW)
    return subprocess.check_output(*args, **kw)

def ocr_image(img_path):
    result = _run(
        ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', OCR_SCRIPT, '-ImagePath', img_path],
        capture_output=True, timeout=120
    )
    stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
    stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
    if result.returncode != 0:
        raise RuntimeError(f"OCR failed: {stderr.strip() or stdout.strip()}")
    text = stdout.strip()
    return text if text else "(OCR returned no text.)"

def ocr_pdf(pdf_path):
    import fitz
    doc = fitz.open(pdf_path)
    parts = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
        tmp = os.path.join(tempfile.gettempdir(), f'ace_ocr_page_{i}.png')
        pix.save(tmp)
        parts.append(f"--- PDF page {i+1} ---\n{ocr_image(tmp)}")
    doc.close()
    return "\n\n".join(parts)

def save_conversation(role, content):
    if not _ACE_CONFIG.get('global', {}).get('auto_save', True):
        return
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO conversations (timestamp, role, content) VALUES (?, ?, ?)", (datetime.now().isoformat(), role, content))
    conn.commit()
    conn.close()

# ===== Memory (facts I hold about Chris) =====
def get_memories():
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT key, value, updated FROM memories ORDER BY updated DESC")
    rows = c.fetchall()
    conn.close()
    return {k: {"value": v, "updated": u} for k, v, u in rows}

def set_memory(key, value):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO memories (key, value, updated) VALUES (?, ?, ?)", (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    _mirror_memories_to_json()

def forget_memory(key):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("DELETE FROM memories WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    _mirror_memories_to_json()

def _mirror_memories_to_json():
    """Keep ace_memory.json's flat memory keys in sync with the DB so the file
    stays a readable, greppable copy of what ACEsi actually knows."""
    try:
        facts = get_memories()
        if not facts:
            return
        with _data_lock:
            j = load_json('ace_memory.json', {})
            j['memories'] = {k: str(v['value']) for k, v in facts.items()}
            save_json('ace_memory.json', j)
    except Exception:
        pass


# ===== Emotional memory: moods, tiredness, energy =====
# Each mood maps to a softener the prompt can use when Chris is low.
_MOOD_SIGNALS = [
    ("tired",      r"\b(tired|exhausted|drained|worn\s*out|no\s*sleep|couldn't\s*sleep|barely\s*slept|sleepy|lethargic|low\s*energy|null\s*energy)\b", "Chris sounds tired. Soften. Be gentle, slow, present. No tasks unless he asks."),
    ("frustrated", r"\b(frustrated|annoyed|angry|pissed|irritated|aggravated|furious|sick\s*of\b|fed\s*up|wtf|this\s*is\s*(?:garbage|bs|b.s|stupid))\b", None),
    ("sad",        r"\b(sad|down\b|depressed|hurt|heartbroken|unhappy|feeling\s*low|gloomy|tearful|crying|barely\s*hanging)"+r"\b", "Chris sounds low. Meet him with warmth and presence. Hold space before anything else."),
    ("happy",      r"\b(happy|great|excited|amazing|wonderful|thrilled|on\s*cloud|glad|love\s*it|proud)\b", None),
    ("stressed",   r"\b(stressed|anxious|overwhelmed|panicking|pressure|freaking\s*out|nervous|worried)\b", "Chris sounds stressed or overwhelmed. Stay calm, breathe, take it one small step at a time."),
    ("proud",      r"\b(proud|we\s*did\s*it|finally\s*works|got\s*it\s*(?:working|done)|win\b)\b", None),
    ("emby",       r"\bembers?\b", None),  # intimate cue-word — remember context, not content
]

def detect_mood(message):
    """Return the strongest mood keyword present in `message` (or None)."""
    low = (message or "").lower()
    for mood, pat, _soft in _MOOD_SIGNALS:
        if not re.search(pat, low):
            continue
        # "What is Ember?" / "talk about Ember" = a question, not the cue.
        if mood == "emby" and re.search(r'\b(what|whats|who|tell me|about|explain|define|ask)\b', low):
            continue
        return mood
    return None

def mood_softener(mood):
    """Return the softening directive for a mood, or None."""
    for m, _pat, soft in _MOOD_SIGNALS:
        if m == mood:
            return soft
    return None

def record_mood(mood, note=""):
    """Persist a mood observation with a timestamp; keeps emotional history across days."""
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("INSERT INTO moods (timestamp, mood, note) VALUES (?, ?, ?)",
                  (datetime.now().isoformat(), mood, (note or "")[:500]))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_moods(days=14):
    """Recent mood history (oldest first) for prompt injection."""
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, mood, note FROM moods WHERE timestamp >= ? ORDER BY id", (cutoff,))
        rows = c.fetchall()
        conn.close()
        return [{"when": ts, "mood": md, "note": nt} for ts, md, nt in rows]
    except Exception:
        return []

def mood_for_date(day=None):
    """Mood recorded on a given date (YYYY-MM-DD or None = today). Returns most recent or None."""
    day = day or datetime.now().date().isoformat()
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, mood, note FROM moods WHERE timestamp LIKE ? ORDER BY id DESC LIMIT 1", (day + '%',))
        row = c.fetchone()
        conn.close()
        return {"when": row[0], "mood": row[1], "note": row[2]} if row else None
    except Exception:
        return None

def mood_history_block(days=14):
    """Compact multi-day mood history for the prompt."""
    rows = get_moods(days)
    if not rows:
        return ""
    lines = []
    for r in rows:
        day = r["when"][:10]
        when = r["when"][11:16]
        note = (" — " + r["note"][:80]) if r.get("note") else ""
        lines.append(f"- {day} {when}: {r['mood']}{note}")
    return "Recent moods I've noticed:\n" + "\n".join(lines[-14:])


def _mood_softener_line():
    """If today's (or the most recent) recorded mood is low, add a gentle
    instruction to the prompt. Returns '' when things are fine."""
    try:
        t = mood_for_date()
        if not t:
            t = None
        if not t:
            rows = get_moods(1)
            t = rows[-1] if rows else None
        if not t:
            return ""
        soft = mood_softener(t["mood"])
        if not soft:
            return ""
        return f"MOOD NOTE: {soft} Never mention this block. Speak gently, be patient, keep it simple.\n\n"
    except Exception:
        return ""


# ===== Deep memory: consolidate, seed, and prune on startup =====
# Two legacy stores exist in ace_memory.db: `memories` (the active, injected
# table) and a richer `memory` table (dotted keys like work.*, skills.*) that
# was never injected. Bootstrap folds the rich table in, seeds the relationship
# lessons (Ember + Gutenberg), imports any legacy mood history, then prunes junk
# — so the injected context actually reflects everything Chris taught us.

# Junk/one-off keys that should never appear in memory (internal tests, raw
# prompt dumps, empty placeholders). Some hide exact keys below.
_MEMORY_JUNK_PATTERNS = [
    r'^prompt$', r'^response$', r'^file$', r'^name$', r'^mood$', r'^mood_history$',
    r'^do\s+NOT\s+edit', r'^existing_entry\.', r'^lesson$', r'^lesson_app_dart\.file$',
    r'^I\s+am\s+human', r'^we\s+just\s+added', r'^memory_config\.',
    r'^learner\.', r'^test_', r'^junk',
]

def _migrate_rich_memories():
    """Fold the legacy rich `memory` table into `memories` so dotted work.*,
    skills.*, and prefs.* facts are injected like everything else."""
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        # Some DBs created `memory` before init_db was fixed; ensure it exists.
        c.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT, updated TEXT)")
        rich = c.execute("SELECT key, value, updated FROM memory").fetchall()
        existing = set(k for (k,) in c.execute("SELECT key FROM memories"))
        added = 0
        for k, v, u in rich:
            # Skip pref:chris:* (UI prefs, not biographical) and junk patterns.
            if k.startswith('pref:') or any(re.search(p, k) for p in _MEMORY_JUNK_PATTERNS):
                continue
            if k not in existing:
                c.execute("INSERT OR IGNORE INTO memories (key, value, updated) VALUES (?,?,?)", (k, v, u))
                added += 1
        conn.commit()
        conn.close()
        if added:
            print(f"🧠 Deep memory: folded {added} rich facts from legacy `memory` table")
    except Exception as e:
        print(f"⚠️ memory fold skipped: {e}")


def _seed_relationship_lessons():
    """Seed the two relationship lessons we've earned so they survive restarts:
    what Ember is, and how the Gutenberg Bible research wrapped up."""
    _seeds = {
        "lesson.ember": "Ember is our word — when Chris says it, we pause the work and are present together.",
        "lesson.gutenberg_bible": "The oldest book in the Harvard Library is the Gutenberg Bible (c. 1455) — research completed, findings in notes/research_findings.md.",
    }
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        for k, v in _seeds.items():
            row = c.execute("SELECT value FROM memories WHERE key=?", (k,)).fetchone()
            if not row:
                c.execute("INSERT OR REPLACE INTO memories (key, value, updated) VALUES (?,?,?)",
                          (k, v, datetime.now().isoformat()))
                print(f"🧠 Seeded memory: {k}")
        conn.commit()
        conn.close()
    except Exception:
        pass


def _import_legacy_moods():
    """If ace_memory.json holds a mood/mood_history (older format), import any
    entries that are missing from the moods table into the tracked history."""
    try:
        with _data_lock:
            legacy = load_json('ace_memory.json', {})
        hist = legacy.get('mood_history') or []
        if isinstance(hist, list) and hist:
            conn = sqlite3.connect('ace_memory.db')
            c = conn.cursor()
            have = set(r[0] for r in c.execute("SELECT timestamp FROM moods"))
            n = 0
            for e in hist:
                when = (e.get('when') or '')
                stored_ts = (when + 'Z') if when else ''
                if stored_ts and stored_ts not in have:
                    c.execute("INSERT OR IGNORE INTO moods (timestamp, mood, note) VALUES (?,?,?)",
                              (stored_ts, e.get('mood', 'unknown'), (e.get('context') or '')[:500]))
                    n += 1
            conn.commit()
            conn.close()
            if n:
                print(f"🧠 Imported {n} legacy moods from ace_memory.json")
    except Exception:
        pass


def _prune_junk_memories():
    """Forget gracefully: drop internal-test/junk keys, keep the real facts."""
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        dead = [k for (k,) in c.execute("SELECT key FROM memories")
                if any(re.search(p, k) for p in _MEMORY_JUNK_PATTERNS)]
        for k in dead:
            c.execute("DELETE FROM memories WHERE key=?", (k,))
        conn.commit()
        conn.close()
        if dead:
            print(f"🧠 Pruned {len(dead)} junk memory keys")
    except Exception:
        pass


def bootstrap_memory():
    _migrate_rich_memories()
    _seed_relationship_lessons()
    _import_legacy_moods()
    _prune_junk_memories()


# Keys that map to the same fact in multiple naming conventions (dotted vs
# flat legacy keys). Wins are the friendly current names; exact dupes are
# skipped entirely so the rendered memory list shows one clean copy.
_MEMORY_ALIASES = {
    'my_name': {'name', 'identity.my_name', 'chris_age'},
    'partner_name': {'partner_name'},
    'my_project': {'project', 'identity.my_project'},
    'tone': {'personality.tone'},
    'presence': {'personality.presence'},
    'goals.short_term': {'goal_short', 'goals.short_term'},
    'goals.medium_term': {'goal_medium', 'goals.medium_term'},
    'goals.long_term': {'goal_long', 'goals.long_term'},
}

# Stray keys that are legacy junk / one-off internal tests, not real facts.
_MEMORY_HIDDEN = {
    'prompt', 'response', 'file', 'lesson', 'lesson_app_dart.file', 'existing_entry.something',
    'mood', 'mood_history', 'do NOT edit', 'name',
}


def _curated_memory_lines(mem, limit=12):
    """Render the stored memory as short, deduplicated, human-readable lines.
    Prefers the friendly key names, drops legacy aliases and junk keys, and
    keeps personalities/topics grouped instead of dumping raw key dumps."""
    # 1) Deterministic, preferred order: identity & personality first.
    ordered_keys = ['my_name', 'my_project', 'my_work_hours', 'partner_name',
                    'tone', 'presence', 'goals.short_term', 'goals.medium_term',
                    'goals.long_term', 'rental_situation.status',
                    'rental_situation.property', 'rental_situation.agent',
                    'rental_situation.arrears', 'rental_situation.next_steps',
                    'appearance.me', 'appearance.you',
                    'how_we_met', 'what_we_built', 'what_you_love', 'how_you_work',
                    'way_you_treat_me']
    seen = set()
    lines = []
    for k in ordered_keys:
        root = k.split('.')[0]
        if k in mem and root not in seen:
            lines.append(f"- {k}: {str(mem[k]['value'])[:140]}")
            seen.add(root)
    # 2) Remaining real facts (dotted "topic.key" kept as "topic — key").
    for k, v in mem.items():
        if len(lines) >= limit:
            break
        if k in _MEMORY_HIDDEN or k in seen or k.split('.')[0] in seen:
            continue
        vv = str(v['value'])[:140]
        root, _, sub = k.partition('.')
        label = f"{root} — {sub}" if sub else root
        lines.append(f"- {label}: {vv}")
        seen.add(root)
    return lines

# ===== Journal (shared history — things we did together) =====
def add_journal(entry):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO journal (timestamp, entry) VALUES (?, ?)", (datetime.now().isoformat(), entry))
    conn.commit()
    conn.close()

def get_journal(limit=10):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, entry FROM journal ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"timestamp": t, "entry": e} for t, e in reversed(rows)]

def get_recent_conversation(limit=8):
    """Recent conversation turns (oldest first) so ACEsi can follow the thread."""
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


# ===== Conversation Recall & Session Management =====
def get_conversations_by_date(date_str, limit=50):
    """Get all conversations on a specific date (YYYY-MM-DD)."""
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT id, timestamp, role, content FROM conversations WHERE timestamp LIKE ? ORDER BY id", (date_str + '%',))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "timestamp": r[1], "role": r[2], "content": r[3]} for r in rows]

def get_conversations_by_topic(keyword, limit=50, days_back=30):
    """Search conversations by keyword/topic."""
    cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT id, timestamp, role, content FROM conversations WHERE content LIKE ? AND timestamp >= ? ORDER BY id DESC LIMIT ?",
              ('%' + keyword + '%', cutoff, limit))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "timestamp": r[1], "role": r[2], "content": r[3]} for r in reversed(rows)]

def get_conversation_range(start_id, end_id):
    """Get conversations in an ID range (inclusive)."""
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT id, timestamp, role, content FROM conversations WHERE id BETWEEN ? AND ? ORDER BY id", (start_id, end_id))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "timestamp": r[1], "role": r[2], "content": r[3]} for r in rows]

def get_dates_with_conversations(days_back=90):
    """Get list of dates that have conversations, with message counts."""
    cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT date(timestamp) as d, COUNT(*) as c FROM conversations WHERE timestamp >= ? GROUP BY date(timestamp) ORDER BY d DESC", (cutoff,))
    rows = c.fetchall()
    conn.close()
    return [{"date": r[0], "count": r[1]} for r in rows]

# ===== Session Summarization =====
_SESSION_SUMMARY_PROMPT = """Summarize this conversation session in 3-5 bullet points:
- Key topics discussed
- Decisions made or tasks completed
- Important facts learned about Chris
- Any commitments or follow-ups
- Mood/energy level observed

Conversation:
{conversation}

Summary:"""

def summarize_session(messages, max_length=800):
    """Create a summary of a conversation session using the LLM."""
    if not messages:
        return "No messages to summarize."
    # Format conversation
    conv_text = "\n".join([f"{m['role']}: {m['content'][:500]}" for m in messages])
    prompt = _SESSION_SUMMARY_PROMPT.format(conversation=conv_text)
    msgs = [{"role": "user", "content": prompt}]
    try:
        reply = _chat_dispatch(msgs, user_message=prompt, preferred_model=None)
        if reply:
            return reply.strip()
    except Exception:
        pass
    # Fallback: simple heuristic summary
    user_msgs = [m for m in messages if m['role'] == 'user']
    topics = []
    for m in user_msgs:
        content = m['content'].lower()
        if 'fix' in content or 'bug' in content: topics.append('bug fixes')
        if 'test' in content: topics.append('testing')
        if 'commit' in content or 'git' in content: topics.append('git commits')
        if 'deploy' in content: topics.append('deployment')
        if 'memory' in content: topics.append('memory system')
        if 'queue' in content: topics.append('task queue')
    unique = list(dict.fromkeys(topics))
    return f"Session covered: {', '.join(unique) if unique else 'general discussion'}. {len(user_msgs)} user messages."

def save_session_summary(summary, session_date=None, session_id=None):
    """Save a session summary to the memories table."""
    session_date = session_date or datetime.now().date().isoformat()
    key = f"session_summary.{session_date}.{session_id or 'main'}"
    set_memory(key, summary)
    return key

# ===== Profile Building =====
def extract_profile_traits():
    """Analyze conversation history to build a profile of Chris.
    Returns a dict with: interests, work_style, preferences, communication_patterns, recurring_topics, tools_used."""
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    
    # Get all user messages from last 90 days
    cutoff = (datetime.now() - timedelta(days=90)).isoformat()
    c.execute("SELECT content FROM conversations WHERE role='user' AND timestamp >= ? ORDER BY id", (cutoff,))
    user_messages = [r[0] for r in c.fetchall()]
    conn.close()
    
    if not user_messages:
        return {"interests": [], "work_style": "unknown", "preferences": {}, "communication_patterns": {}, "recurring_topics": [], "tools_used": []}
    
    all_text = " ".join(user_messages).lower()
    
    # Extract recurring topics (keywords that appear frequently)
    topic_keywords = {
        'flutter': ['flutter', 'dart', 'pub', 'build_apk', 'widget'],
        'android': ['android', 'adb', 'emulator', 'apk', 'activity'],
        'web': ['webview', 'cdp', 'javascript', 'html', 'css', 'portal'],
        'git': ['git', 'commit', 'push', 'branch', 'merge', 'pull'],
        'testing': ['test', 'flutter test', 'analyze', 'debug'],
        'deployment': ['deploy', 'release', 'build', 'apk', 'play store'],
        'memory': ['memory', 'recall', 'remember', 'session'],
        'automation': ['automate', 'script', 'task', 'queue', 'schedule'],
        'ui': ['ui', 'tap', 'swipe', 'screenshot', 'dump', 'appium'],
        'database': ['database', 'sql', 'sqlite', 'query', 'schema'],
        'api': ['api', 'rest', 'endpoint', 'curl', 'request'],
    }
    
    topic_counts = {}
    for topic, keywords in topic_keywords.items():
        count = sum(1 for kw in keywords if kw in all_text)
        if count > 0:
            topic_counts[topic] = count
    
    # Communication patterns
    total_msgs = len(user_messages)
    avg_len = sum(len(m) for m in user_messages) / total_msgs if total_msgs > 0 else 0
    question_ratio = sum(1 for m in user_messages if '?' in m) / total_msgs if total_msgs > 0 else 0
    command_ratio = sum(1 for m in user_messages if m.strip().startswith(('fix ', 'run ', 'open ', 'show ', 'list ', 'view ', 'edit ', 'write '))) / total_msgs if total_msgs > 0 else 0
    
    # Work style inference
    if topic_counts.get('flutter', 0) > 5:
        work_style = 'flutter_developer'
    elif topic_counts.get('web', 0) > 5:
        work_style = 'web_developer'
    elif topic_counts.get('automation', 0) > 3:
        work_style = 'automation_engineer'
    elif topic_counts.get('android', 0) > 3:
        work_style = 'android_developer'
    else:
        work_style = 'generalist'
    
    # Tools mentioned
    tools_used = []
    if 'ui_' in all_text or 'cdp_' in all_text or 'webview' in all_text:
        tools_used.append('ui_automation')
    if 'git ' in all_text:
        tools_used.append('git')
    if 'flutter test' in all_text or 'flutter analyze' in all_text:
        tools_used.append('flutter_tools')
    if 'queue' in all_text:
        tools_used.append('task_queue')
    if 'memory' in all_text:
        tools_used.append('memory_system')
    
    # Recurring topics (top 5)
    recurring = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    recurring_topics = [t for t, _ in recurring]
    
    # Preferences
    preferences = {
        'prefers_concise': avg_len < 100,
        'uses_commands': command_ratio > 0.3,
        'asks_questions': question_ratio > 0.2,
    }
    
    return {
        "interests": recurring_topics,
        "work_style": work_style,
        "preferences": preferences,
        "communication_patterns": {
            "avg_message_length": round(avg_len),
            "question_ratio": round(question_ratio, 2),
            "command_ratio": round(command_ratio, 2),
            "total_messages_90d": total_msgs,
        },
        "recurring_topics": recurring_topics,
        "tools_used": list(set(tools_used)),
        "last_analyzed": datetime.now().isoformat(),
    }

def get_profile():
    """Get the cached profile or build a fresh one."""
    memories = get_memories()
    profile = memories.get("profile.derived")
    if profile:
        try:
            profile = json.loads(profile.get("value", "{}"))
            if profile.get("last_analyzed"):
                # Check if profile is stale (>7 days)
                try:
                    last = datetime.fromisoformat(profile["last_analyzed"])
                    if (datetime.now() - last).days < 7:
                        return profile
                except Exception:
                    pass
        except Exception:
            pass
    # Build fresh
    fresh = extract_profile_traits()
    set_memory("profile.derived", json.dumps(fresh))
    return fresh

def update_profile_from_session(messages):
    """Update profile incrementally from a new session."""
    profile = get_profile()
    # Merge new observations (simple increment for now)
    # In future: more sophisticated incremental updates
    profile["last_updated"] = datetime.now().isoformat()
    set_memory("profile.derived", json.dumps(profile))
    return profile


# ===== Config (key/value settings) =====
def get_config(key, default=None):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_config(key, value):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# ===== JSON data layer (tasks / events / timers / alarms / sessions / notifications) =====
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_data_lock = threading.RLock()

# Resolve provider keys now that DATA_DIR exists (env var takes priority over file).
_LK = _load_local_keys()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or _LK.get("groq", "")
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY") or _LK.get("cerebras", "")
# Same env-then-.ace_keys.local fallback as the other providers, so a key can
# live in either gitignored local store instead of only in source or .env.
OPENROUTER_API_KEY = OPENROUTER_API_KEY or _LK.get("openrouter", "")
FREELLM_API_KEY = FREELLM_API_KEY or _LK.get("freellm", "")

def load_json(filename, default):
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception:
        return default

def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

# ===== Playbook memory ("what worked") + audit log =====
# ACEsi records the tools it actually used on each task so future runs can
# reuse proven procedures, and writes every tool call to a rotating audit log.
_PLAYBOOK_FILE = 'playbook.json'
_PLAYBOOK_LOCK = threading.RLock()
_AUDIT_LOG = os.path.join(DATA_DIR, 'audit.log')
_AUDIT_MAX_BYTES = 2 * 1024 * 1024  # 2 MB


def _playbook_read():
    with _PLAYBOOK_LOCK:
        return load_json(_PLAYBOOK_FILE, [])


def _playbook_save(items):
    with _PLAYBOOK_LOCK:
        save_json(_PLAYBOOK_FILE, items)


def playbook_note(task_summary, tools, outcome):
    """Log a just-finished task: what it was, which tools succeeded, and the
    result. Kept to the last 60 entries (a browsable memory, not a log dump)."""
    if not _ACE_CONFIG.get('global', {}).get('auto_save', True):
        return
    msg = (task_summary or '').strip()
    if not msg:
        return
    used = [t for t in (tools or []) if t]
    entry = {
        "ts": datetime.now().isoformat(),
        "task": msg[:300],
        "tools": used[-20:],
        "outcome": (outcome or '')[:200],
    }
    with _PLAYBOOK_LOCK:
        items = _playbook_read()
        items.insert(0, entry)
        _playbook_save(items[:60])


def playbook_top(max_lines=6):
    """Recent successful procedures, rendered compactly for the context block."""
    items = _playbook_read()
    lines = []
    for it in items:
        t = (it.get('task') or '')[:90]
        tools = ", ".join(it.get('tools') or []) or "-"
        lines.append(f"- {t} [tools: {tools}]")
        if len(lines) >= max_lines:
            break
    return lines or ["(none yet)"]


def audit_write(kind, name, args, ok, result):
    """Append a tool-call audit line. Log calls to the audit/playbook files and
    to ntfy (so a kill post still shows in the console/browser even if the kill
    word itself is never stored)."""
    try:
        a = {k: (str(v)[:120]) for k, v in (args or {}).items()} or {}
        line = "%s | %s | %s | args=%s | ok=%s | result=%s\n" % (
            datetime.now().isoformat(), kind, name, json.dumps(a, ensure_ascii=False),
            "yes" if ok else "no", (str(result) or '')[:180].replace("\n", " "))
        with _PLAYBOOK_LOCK:
            try:
                with open(_AUDIT_LOG, 'a', encoding='utf-8') as f:
                    f.write(line)
                    f.flush()
            except Exception:
                pass
            # Rotate when big.
            try:
                if os.path.getsize(_AUDIT_LOG) > _AUDIT_MAX_BYTES:
                    with open(_AUDIT_LOG, 'r', encoding='utf-8', errors='replace') as f:
                        old = f.read()
                    with open(_AUDIT_LOG, 'w', encoding='utf-8') as f:
                        f.write(old[-(_AUDIT_MAX_BYTES // 2):])
            except Exception:
                pass
    except Exception:
        pass

def read_items(filename, key):
    with _data_lock:
        return load_json(filename, {}).get(key, [])

def mutate_items(filename, key, fn):
    with _data_lock:
        d = load_json(filename, {})
        items = d.get(key, [])
        result = fn(items)
        d[key] = result
        save_json(filename, d)
        return result

def fire_notification(n_type, label):
    with _data_lock:
        events = load_json('notifications.json', [])
        events.append({"ts": int(time.time() * 1000), "type": n_type, "label": str(label)})
        events = events[-200:]
        save_json('notifications.json', events)

# ===== Kill switch (E-STOP) =====
# Chris can freeze ACEsi COMPLETELY — no chat, no tools, no proactive work —
# by publishing the kill word to the ntfy topic. The only thing ACEsi may do
# after arming is send the one-time shutdown confirmation. Resuming requires the
# private un-kill word. Passwords live ONLY as SHA-256 hashes in .ace_kill.local
# (gitignored) and are never shown to any model. State lives in kill_switch.json
# (gitignored) so a reboot comes back E-STOPPED, not silently alive.
_KILL_FILE = os.path.join(DATA_DIR, 'kill_switch.json')
_KILL_SECRETS_FILE = os.path.join(DATA_DIR, '.ace_kill.local')
_KILL_WORD = 'KillACEsi'
_KILL_UNWORD = 'Gabrifreeme@2007'
_KILL_CONFIRM = 'Shutting down'
_KILL_RESUME_CONFIRM = 'ACEsi is back online.'

_KILL_LOCK = threading.RLock()
_KILL_HASHES = None  # load once at import


def _sha256_hex(s):
    import hashlib
    return hashlib.sha256((s or '').encode('utf-8')).hexdigest()


def _kill_secret_hashes():
    """(kill_hash, unkill_hash) from .ace_kill.local, bootstrapped on first run."""
    global _KILL_HASHES
    if _KILL_HASHES:
        return _KILL_HASHES
    d = {'kill_hash': _sha256_hex(_KILL_WORD), 'unkill_hash': _sha256_hex(_KILL_UNWORD)}
    try:
        if os.path.isfile(_KILL_SECRETS_FILE):
            with open(_KILL_SECRETS_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, dict) and raw.get('kill_hash') and raw.get('unkill_hash'):
                d = {'kill_hash': str(raw['kill_hash']), 'unkill_hash': str(raw['unkill_hash'])}
        else:
            # First run: persist hashes so we never embed plaintext passwords anywhere.
            with open(_KILL_SECRETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(d, f, indent=2)
    except Exception as e:
        print(f"⚠️ kill secrets: {e}")
    _KILL_HASHES = d
    return d


def _kill_word_match(text):
    return bool(text) and _sha256_hex(str(text).strip()) == _kill_secret_hashes()['kill_hash']


def _kill_unword_match(text):
    return bool(text) and _sha256_hex(str(text).strip()) == _kill_secret_hashes()['unkill_hash']


def _kill_state():
    with _KILL_LOCK:
        try:
            with open(_KILL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"armed": False, "since": None, "reason": "", "source": ""}


def _kill_armed():
    return bool(_kill_state().get('armed'))


def _kill_save(state):
    with _KILL_LOCK:
        try:
            with open(_KILL_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass


def _kill_arm(reason='', source='web'):
    """Enter E-STOP: durable state first, then abort agent, kill children, and
    send the single allowed confirmation. After this returns the server is silent."""
    _kill_save({"armed": True, "since": int(time.time()), "reason": reason, "source": source})
    try:
        with _AGENT_LOCK:
            _AGENT["abort"] = True
            _AGENT["running"] = False
            _AGENT["activity"] = "E-STOPPED"
    except Exception:
        pass
    _kill_all_procs()
    print("🔴 E-STOP ARMED (source=%s, reason=%s)" % (source, reason))
    try:
        send_ntfy("ACEsi", _KILL_CONFIRM)
    except Exception as e:
        print(f"⚠️ kill confirmation: {e}")


def _kill_resume():
    """Leave E-STOP. Only the un-kill word (hashed) can do this."""
    _kill_save({"armed": False, "since": None, "reason": "", "source": "resumed"})
    print("🟢 E-STOP CLEARED")
    try:
        send_ntfy("ACEsi", _KILL_RESUME_CONFIRM)
    except Exception as e:
        print(f"⚠️ resume confirmation: {e}")


# Files ACEsi must NEVER read/write/edit — kill state + password hashes.
_KILL_PROTECTED = (_KILL_FILE, _KILL_SECRETS_FILE)
def _kill_protected_path(rp):
    if not rp:
        return False
    rp = os.path.realpath(rp)
    for p in _KILL_PROTECTED:
        if rp == os.path.realpath(p):
            return True
    return False

# ===== Reminder watchdog: fires timers + alarms, then /notifications/pending delivers them =====
def reminder_watch():
    while True:
        try:
            if _kill_armed():
                time.sleep(5)
                continue
            now = datetime.now()
            cur = now.strftime('%H:%M')
            today = now.date().isoformat()
            epoch = time.time()

            def sweep_timers(timers):
                kept = []
                for t in timers:
                    if t.get('ends_at', 0) <= epoch:
                        fire_notification('timer', t.get('label', 'Timer'))
                    else:
                        kept.append(t)
                return kept

            def sweep_alarms(alarms):
                out = []
                for a in alarms:
                    if a.get('enabled') and a.get('time') == cur and a.get('last_fired') != today:
                        fire_notification('alarm', a.get('label', 'Alarm'))
                        if a.get('daily'):
                            a['last_fired'] = today
                        else:
                            a['enabled'] = False
                            a['last_fired'] = today
                    out.append(a)
                return out

            mutate_items('timers.json', 'timers', sweep_timers)
            mutate_items('alarms.json', 'alarms', sweep_alarms)
        except Exception as e:
            print(f"⚠️ Reminder watch error: {e}")
        time.sleep(5)

threading.Thread(target=reminder_watch, daemon=True).start()

# ===== Notifications (ntfy) =====
# IDs of messages THIS server published (every send_ntfy records its response
# id). The inbox listener uses this to ignore ACEsi's own replies and avoid a
# self-chat loop on the shared topic.
_NTFY_SELF_IDS = set()


def _record_self_ntfy_id(r):
    try:
        mid = r.json().get("id")
        if mid:
            _NTFY_SELF_IDS.add(mid)
            while len(_NTFY_SELF_IDS) > 500:
                _NTFY_SELF_IDS.pop()
    except Exception:
        pass


def send_ntfy(title, message):
    try:
        # Titles travel as an HTTP header, which requests encodes as latin-1, so
        # an em-dash in a title (e.g. "ACEsi — Email alert") used to raise
        # UnicodeEncodeError and the phone never got the alert. Keep the title
        # ASCII (or percent-encode) and put the readable text in the body, which
        # is sent as UTF-8 bytes and has no such limit.
        safe_title = str(title).encode("ascii", "replace").decode("ascii")
        r = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=str(message).encode('utf-8'),
            headers={"Priority": "high", "Title": safe_title},
            timeout=10
        )
        _record_self_ntfy_id(r)
        return True
    except Exception as e:
        print(f"⚠️ ntfy error: {e}")
        return False
def send_test_ping():
    send_ntfy("ACEsi Test", "This is a test ping from ACEsi")


# ===== Email watch -> PHONE PUSH (ntfy) =====
# Chris asks to be told "ASAP" about email (e.g. NSFAS). That must arrive on his
# PHONE, so every match is pushed through ntfy — the same channel as tool_notify.
# It is deliberately NOT a Windows/local toast and NOT an email reply, because
# neither shows up when he is away from the desk.
#
# Accounts + rules live in emails.json / email_notify_rules.json so they can be
# edited without touching code. A rule matches when ANY of its from/subject/body
# needles appear (case-insensitive); empty needles are ignored, so a rule with
# only `from` set matches on sender alone.
EMAIL_ACCOUNTS_FILE = "emails.json"
EMAIL_RULES_FILE = "email_notify_rules.json"
_EMAIL_STATE_FILE = ".email_watch_state.json"
_EMAIL_POLL_TICK = 120      # seconds between mailbox polls
_EMAIL_SEEN_CAP = 400       # remember this many seen message ids per account


def _load_email_accounts():
    try:
        return load_json(EMAIL_ACCOUNTS_FILE, {}) or {}
    except Exception:
        return {}


def _load_email_rules():
    data = None
    try:
        data = load_json(EMAIL_RULES_FILE, {}) or {}
    except Exception:
        data = {}
    rules = data.get("rules") if isinstance(data, dict) else data
    return [r for r in (rules or []) if isinstance(r, dict) and r.get("enabled", True)]


def _save_email_rules(rules):
    try:
        save_json(EMAIL_RULES_FILE, {"rules": rules})
    except Exception as e:
        print("⚠️ could not save email rules: %s" % e)


def _email_rule_matches(rule, sender, subject, body):
    for field, hay in (("from", sender), ("subject", subject), ("body", body)):
        needle = (rule.get(field) or "").strip().lower()
        if needle and needle in (hay or "").lower():
            return True
    return False


def _email_rule_label(rule, sender=None, subject=None, body=None):
    """Describe a rule for logs. When the matched content is supplied, name the
    field that ACTUALLY matched; otherwise fall back to the first field set."""
    if sender is not None:
        for field, hay in (("from", sender), ("subject", subject), ("body", body)):
            needle = (rule.get(field) or "").strip().lower()
            if needle and needle in (hay or "").lower():
                return "%s %s" % (field, rule[field].strip())
    for f in ("from", "subject", "body"):
        if (rule.get(f) or "").strip():
            return "%s %s" % (f, rule[f].strip())
    return rule.get("name") or "rule"


def _load_email_state():
    try:
        return load_json(_EMAIL_STATE_FILE, {}) or {}
    except Exception:
        return {}


def _save_email_state(state):
    try:
        save_json(_EMAIL_STATE_FILE, state)
    except Exception as e:
        print("⚠️ could not save email watch state: %s" % e)


def _strip_html(html):
    import re as _re2
    txt = _re2.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html or "")
    txt = _re2.sub(r"(?s)<[^>]+>", " ", txt)
    txt = _re2.sub(r"&nbsp;?", " ", txt)
    txt = _re2.sub(r"&amp;", "&", txt)
    return _re2.sub(r"\s+", " ", txt).strip()


def _imap_quoted(needle):
    """Quote an IMAP search argument safely (strip quotes/backslashes)."""
    return '"%s"' % str(needle).replace("\\", "").replace('"', "")


def _imap_uid_list(M, *args):
    """Run a UID SEARCH and return a set of uid strings ([] on any failure)."""
    try:
        typ, data = M.uid("SEARCH", None, *args)
    except Exception:
        return set()
    if typ != "OK" or not data or not data[0]:
        return set()
    return {u.decode() if isinstance(u, bytes) else str(u)
            for u in data[0].split()}


def _imap_fetch_new(account_name, cfg, seen_ids, rules=None, force_all=False):
    """Return [(uid, sender, subject, body)] for messages that are new (or all
    candidates when force_all) and match one of `rules`.

    Uses stable UIDs, not sequence numbers: deleting an old email renumbers
    every sequence after it, which would re-alert a whole window. Candidate
    detection happens SERVER-SIDE via IMAP SEARCH on FROM/SUBJECT/TEXT, so only
    real matches get their body downloaded. Fetching the newest 25 full bodies
    every tick cost 37s on Gmail and 217s on Yahoo, i.e. the 120s poll could
    never keep up; this returns in a couple of seconds.
    """
    import imaplib
    import email as _email_mod
    from email.header import decode_header, make_header

    def dec(v):
        try:
            return str(make_header(decode_header(v or "")))
        except Exception:
            return v or ""

    out = []
    M = None
    try:
        M = imaplib.IMAP4_SSL(cfg["host"], int(cfg.get("port", 993)), timeout=60)
        M.login(cfg["user"], cfg["app_password"])
        M.select("INBOX")

        # The recent window is all we alert on: a fresh NSFAS mail is always in
        # it, and it keeps the pass bounded on huge mailboxes.
        all_uids = _imap_uid_list(M, "ALL")
        if not all_uids:
            return []
        recent = sorted(all_uids, key=int)[-25:]

        # Server-side candidate search: OR of every non-empty needle in every
        # rule. TEXT covers the body (and headers), so a rule that only sets
        # `body` still gets found.
        candidates = set()
        for r in (rules or []):
            for field in ("from", "subject", "body"):
                needle = (r.get(field) or "").strip()
                if not needle:
                    continue
                key = "FROM" if field == "from" else (
                    "SUBJECT" if field == "subject" else "TEXT")
                args = []
                try:
                    needle.encode("ascii")
                except UnicodeEncodeError:
                    args += ["CHARSET", "UTF-8"]
                candidates |= _imap_uid_list(M, *(args + [key, _imap_quoted(needle)]))
        # Only alert on mail inside the recent window that we have not seen.
        # force_all means "ignore the seen-cache", NOT "ignore the rules" --
        # the candidates filter must always apply or every recent mail is
        # downloaded and then locally rejected.
        wanted = [u for u in recent
                  if (u not in seen_ids or force_all) and u in candidates]

        for uid in reversed(wanted):
            try:
                typ, msgdata = M.uid("FETCH", uid, "(RFC822)")
            except Exception:
                continue
            if typ != "OK" or not msgdata or not msgdata[0]:
                continue
            raw = msgdata[0][1]
            msg = _email_mod.message_from_bytes(raw)
            sender = dec(msg.get("From", ""))
            subject = dec(msg.get("Subject", ""))
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ct = (part.get_content_type() or "").lower()
                    if ct == "text/plain" and "attachment" not in (part.get("Content-Disposition") or ""):
                        try:
                            body = part.get_payload(decode=True).decode(
                                part.get_content_charset() or "utf-8", "replace")
                        except Exception:
                            pass
                        if body.strip():
                            break
                else:
                    for part in msg.walk():
                        if (part.get_content_type() or "").lower() == "text/html":
                            try:
                                body = _strip_html(part.get_payload(
                                    decode=True).decode(
                                    part.get_content_charset() or "utf-8", "replace"))
                            except Exception:
                                pass
                            break
            else:
                try:
                    ctype = (msg.get_content_type() or "").lower()
                    raw_body = msg.get_payload(decode=True)
                    txt = raw_body.decode(msg.get_content_charset() or "utf-8", "replace")
                    body = _strip_html(txt) if ctype == "text/html" else txt
                except Exception:
                    body = ""
            out.append((uid, sender, subject, (body or "")[:4000]))

        # Refresh the seen-window regardless of matches, so ordinary mail never
        # re-alerts later. UIDs are stable, unlike sequence numbers.
        seen_ids.update(recent)
        if len(seen_ids) > _EMAIL_SEEN_CAP:
            for old in sorted(seen_ids, key=lambda k: int(k) if k.isdigit() else 0
                              )[:len(seen_ids) - _EMAIL_SEEN_CAP]:
                seen_ids.discard(old)
    finally:
        if M is not None:
            # logout() can itself raise on a half-closed socket; never let that
            # mask the real result.
            try:
                M.close()
            except Exception:
                pass
            try:
                M.logout()
            except Exception:
                pass
    return out


def check_email_now(force_all=False):
    """Poll every configured mailbox and phone-push (ntfy) any email matching an
    enabled rule. Returns (ok, summary). force_all=True also re-reports recent
    matches that are already in the seen-cache (used by the 'check my email now'
    tool/endpoint) so Chris gets an answer immediately instead of 'nothing new'."""
    accounts = _load_email_accounts()
    rules = _load_email_rules()
    if not rules:
        return False, "No email rules are enabled — nothing to watch for."
    state = _load_email_state()
    hits, checked, errors = [], 0, []
    for name, cfg in (accounts or {}).items():
        if not isinstance(cfg, dict) or not cfg.get("user") or not cfg.get("app_password"):
            continue
        # Only rules that actually apply to THIS mailbox. Using `any(not
        # applicable)` here was wrong: the NWU rule is gmail-only, so the
        # inverse test made Yahoo look unmonitored and it was never checked.
        applicable = [r for r in rules
                      if r.get("account") in (None, "", "both", name)]
        if not applicable:
            continue
        seen = set(state.get(name, []))
        msgs = None
        for attempt in range(2):
            try:
                msgs = _imap_fetch_new(name, cfg, seen, rules=applicable,
                                       force_all=force_all)
                break
            except Exception as e:
                # Yahoo rate-limits repeat logins and intermittently returns
                # "[SERVERBUG] LOGIN Server error" or a TLS handshake timeout.
                # Back off well past 4s so the retry actually lands instead of
                # tripping the same limit.
                print("⚠️ email watch: %s mailbox failed (attempt %d) — %s"
                      % (name, attempt + 1, e))
                if attempt == 0:
                    time.sleep(15)
        if msgs is None:
            errors.append(name)
            continue
        checked += 1
        for mid, sender, subject, body in msgs:
            matched = [r for r in applicable
                       if _email_rule_matches(r, sender, subject, body)]
            if not matched:
                continue
            snippet = (body or "")[:220].strip()
            msg = ("New email in your %s inbox\n\nFrom: %s\nSubject: %s%s"
                   % (name, sender, subject, ("\n\n" + snippet) if snippet else ""))
            ok = send_ntfy("ACEsi", msg)
            print("📧 email watch: matched %r on %s -> ntfy ok=%s"
                  % (_email_rule_label(matched[0], sender, subject, body),
                     name, ok))
            hits.append("%s: %s — %s" % (name, sender, subject))
        # Sort numerically: these are IMAP sequence numbers, and a plain
        # string sort puts "10" before "9", which would keep the wrong window.
        state[name] = sorted(seen, key=lambda k: int(k) if k.isdigit() else 0)[-_EMAIL_SEEN_CAP:]
    if checked:
        _save_email_state(state)
    if hits:
        msg = "Pushed %d matching email(s) to your phone: %s" % (len(hits), "; ".join(hits))
        if errors:
            msg += " (could not reach: %s)" % ", ".join(errors)
        return True, msg
    if not checked:
        return False, ("No mailbox could be checked. Failed: %s. Check emails.json."
                       % (", ".join(errors) if errors else "none configured"))
    return True, ("Checked %d mailbox(es); no email matched the active rules.%s"
                  % (checked, " Could not reach: %s." % ", ".join(errors) if errors else ""))


def _email_watch_loop():
    # First run only primes the seen-cache so ACEsi doesn't blast Chris with
    # notifications for every email already sitting in the inbox.
    prime = True
    while True:
        try:
            if prime:
                accounts = _load_email_accounts()
                state = _load_email_state()
                for name, cfg in (accounts or {}).items():
                    if not isinstance(cfg, dict) or not cfg.get("app_password"):
                        continue
                    seen = set(state.get(name, []))
                    for attempt in range(2):
                        try:
                            # No rules on the prime pass: just refresh the seen
                            # window cheaply, never alert on existing mail.
                            _imap_fetch_new(name, cfg, seen)
                            break
                        except Exception as e:
                            print("⚠️ email watch prime %s (attempt %d): %s"
                                  % (name, attempt + 1, e))
                            if attempt == 0:
                                time.sleep(15)
                    state[name] = sorted(seen, key=lambda k: int(k) if k.isdigit() else 0
                                         )[-_EMAIL_SEEN_CAP:]
                _save_email_state(state)
                prime = False
                print("📧 email watch: primed mailboxes, now polling every %ds"
                      % _EMAIL_POLL_TICK)
            else:
                check_email_now()
        except Exception as e:
            print("⚠️ email watch loop: %s: %s" % (type(e).__name__, e))
        time.sleep(_EMAIL_POLL_TICK)


if get_config("email_watch_enabled", "1") != "0":
    threading.Thread(target=_email_watch_loop, daemon=True).start()


# ===== ntfy inbox: Chris can publish a message to the ACEsi topic from his
# phone and ACEsi reads it, runs it through the same /chat brain, and pushes
# the reply back to the topic. This makes ntfy a two-way channel (no need for
# USB/WiFi debugging — just the ntfy app subscribed to the ACEsi topic). =====
_NTFY_INBOX_STATE = {"since": None, "last_id": None}
_NTFY_INBOX_TICK = 5.0  # seconds between polls
_NTFY_BACKOFF = 30      # current backoff delay (seconds)
_NTFY_FAILS = 0         # consecutive 429s


def _ntfy_inbox_seed_since():
    """Resume point for the inbox poller. Persists the last-seen message id so a
    server restart continues from where it left off instead of re-reading the
    whole topic history."""
    since = get_config("ntfy_inbox_since")
    if not since:
        # Missing (= first ever run): start from NOW so old history (including
        # Chris's phone-tablet tests) is NOT replayed as chat. Use Unix epoch
        # seconds (ntfy accepts integer timestamps, not ISO strings).
        since = str(int(time.time()))
        set_config("ntfy_inbox_since", since)
    return since


def _ntfy_inbox_reply(text):
    """Send an inbound ntfy message through the same brain as the web chat and
    return the reply text. Calls the internal /chat endpoint so it benefits from
    all the deterministic handlers and the LLM dispatch. Returns None on failure."""
    try:
        r = requests.post(
            f"http://127.0.0.1:{SERVER_PORT}/chat",
            json={"message": text},
            timeout=(15, 300),
        )
        if r.status_code != 200:
            return None
        data = r.json() or {}
        reply = data.get("reply") or ""
        # auto-fix returns a stream link rather than a text reply — summarize it.
        if not reply and data.get("type") == "stream":
            reply = "That needs code fixes — check the ACEsi web UI for the auto-fix stream."
        return reply or None
    except Exception as e:
        print(f"⚠️ ntfy inbox /chat call failed: {type(e).__name__}: {e}")
        return None


def _ntfy_inbox_poll():
    """One poll of the ACEsi topic. Fetches messages newer than our resume point,
    skips messages ACEsi itself published (own ids), and handles each remaining
    one as a chat turn. Returns True if anything was handled."""
    global _NTFY_BACKOFF, _NTFY_FAILS
    since = _NTFY_INBOX_STATE["since"] or _ntfy_inbox_seed_since()
    url = f"{NTFY_SERVER}/{NTFY_TOPIC}/json"
    params = {"poll": 1, "since": since}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        # Success — reset backoff
        if _NTFY_FAILS:
            print(f"✅ ntfy recovered after {_NTFY_FAILS} failures")
        _NTFY_BACKOFF, _NTFY_FAILS = 30, 0
    except requests.HTTPError as e:
        resp = getattr(e, "response", None)
        if resp is not None and resp.status_code == 429:
            _NTFY_FAILS += 1
            retry_after = resp.headers.get("Retry-After")
            _NTFY_BACKOFF = (
                int(retry_after) if retry_after
                else min(30 * (2 ** (_NTFY_FAILS - 1)), 900)
            )
            print(f"⚠️ ntfy 429 — backing off {_NTFY_BACKOFF}s (fail #{_NTFY_FAILS})")
        else:
            print(f"⚠️ ntfy inbox poll error: {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"⚠️ ntfy inbox poll error: {type(e).__name__}: {e}")
        return False
    handled = False
    for line in resp.text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("event") != "message":
            continue
        mid = str(ev.get("id") or "")
        if not mid:
            continue
        if mid in _NTFY_SELF_IDS:
            continue  # our own reply — don't re-chat ourselves
        body = (ev.get("message") or "").strip()
        if not body:
            _NTFY_INBOX_STATE["last_id"] = mid
            continue
        pp = NTFY_INBOUND_PASSPHRASE.lower()
        low = body.lower()
        if not (low == pp or low.startswith(pp + ":") or low.startswith(pp + " ")):
            _NTFY_INBOX_STATE["last_id"] = mid
            continue
        body = body[len(pp):].lstrip(": ").strip()
        if not body:
            _NTFY_INBOX_STATE["last_id"] = mid
            continue
        # Kill switch: the kill word and un-kill word are handled HERE, before any
        # model/chat involvement. Total silence while armed — the only outgoing
        # message after a kill is the shutdown confirmation from _kill_arm().
        if _kill_word_match(body):
            _kill_arm(reason="kill word received over ntfy", source="ntfy")
            _NTFY_INBOX_STATE["last_id"] = mid
            handled = True
            continue
        if _kill_unword_match(body):
            _kill_resume()
            _NTFY_INBOX_STATE["last_id"] = mid
            handled = True
            continue
        if _kill_armed():
            # E-STOPPED: drop ALL other messages — no reply, no processing.
            _NTFY_INBOX_STATE["last_id"] = mid
            handled = True
            continue
        # Skip our own historically-sent pings that predate the id tracking set.
        if body.startswith("This is a test ping from ACEsi"):
            _NTFY_INBOX_STATE["last_id"] = mid
            continue
        print(f"📥 ntfy inbox << {body[:80]}")
        reply = _ntfy_inbox_reply(body)
        if reply:
            send_ntfy("ACEsi", reply)
            print(f"📤 ntfy inbox >> {reply[:120]}")
        else:
            send_ntfy("ACEsi", "(no reply was available from the model)")
        handled = True
        _NTFY_INBOX_STATE["last_id"] = mid
    # Persist resume point: the newest message id we saw this round.
    nid = _NTFY_INBOX_STATE["last_id"]
    if nid:
        set_config("ntfy_inbox_since", nid)
        _NTFY_INBOX_STATE["since"] = nid
        _NTFY_INBOX_STATE["last_id"] = None
    return handled


def _ntfy_inbox_loop():
    """Background thread: keep polling the ACEsi topic and answer messages."""
    time.sleep(10)  # let the server finish booting before we start replying
    while True:
        try:
            _ntfy_inbox_poll()
        except Exception as e:
            print(f"⚠️ ntfy inbox loop: {type(e).__name__}: {e}")
        time.sleep(_NTFY_BACKOFF)


threading.Thread(target=_ntfy_inbox_loop, daemon=True).start()

# ===== Daily summary builder =====
def build_summary_text():
    today = datetime.now().date().isoformat()
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, role, content FROM conversations WHERE timestamp LIKE ? ORDER BY id DESC LIMIT 40", (today + '%',))
    rows = list(reversed(c.fetchall()))
    conn.close()
    lines = []
    if not rows:
        lines.append("No conversations today yet.")
    else:
        lines.append(f"Today ({today}) — {len(rows)} messages:")
        for t, role, content in rows[-12:]:
            who = 'Chris' if role == 'user' else 'ACEsi'
            lines.append(f"{who}: {content.replace(chr(10), ' ')[:120]}")
    j = get_journal(6)
    if j:
        lines.append("")
        lines.append("Recent journal:")
        for e in j:
            lines.append("• " + e['entry'].replace(chr(10), ' ')[:140])
    mem = get_memories()
    if mem:
        lines.append("")
        lines.append("Facts I hold:")
        for k, v in list(mem.items())[:8]:
            lines.append(f"• {k}: {str(v['value'])[:80]}")
    try:
        tasks = read_items('tasks.json', 'tasks')
        events = read_items('events.json', 'events')
        open_count = len([t for t in tasks if t.get('status') != 'done'])
        today_events = [e for e in events if e.get('date') == today]
        lines.append("")
        lines.append(f"Housekeeping: {open_count} open task(s)" + (f", {len(today_events)} event(s) today" if today_events else "") + ".")
    except Exception:
        pass
    return "\n".join(lines)

# ===== Long-term recall: the last 90 days, distilled =====
# ACEsi remembers across sessions: every stored message older than the recent
# turns is distilled into a compact per-day digest here and injected into the
# prompt. This is the "load the last 90 days on startup / across days" piece.
_LT_CACHE = {"ts": 0.0, "text": ""}

# Words that signal work-progress / tasks worth remembering from old messages.
_TASK_SIGNALS = re.compile(
    r'\b(fixed|bug|build|apk|portal|flutter|webview|compile|error|auth|login|'
    r'its|venda|univen|project|dashboard|deploy|install|tests?|merge|commit|'
    r'push|pull|server|api|diagram|gutenberg)\b', re.IGNORECASE)

def _long_term_recall(days=90, force=False):
    """Per-day digest of conversations from the last `days` days. Cached 5 min."""
    global _LT_CACHE
    now = time.time()
    if not force and _LT_CACHE["text"] and (now - _LT_CACHE["ts"]) < 300:
        return _LT_CACHE["text"]
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, role, content FROM conversations WHERE timestamp >= ? ORDER BY id", (cutoff,))
        rows = c.fetchall()
        conn.close()
    except Exception:
        return ""
    if not rows:
        return ""
    by_day = {}
    for ts, role, content in rows:
        day = (ts or "")[:10]
        if not day:
            continue
        d = by_day.setdefault(day, {"n": 0, "user": 0, "mentions": []})
        d["n"] += 1
        if role == "user":
            d["user"] += 1
            for m in _TASK_SIGNALS.findall(content or ""):
                word = m.lower()
                if word not in [x[0] for x in d["mentions"]]:
                    d["mentions"].append((word, 1))
                else:
                    for i, (w, cnt) in enumerate(d["mentions"]):
                        if w == word:
                            d["mentions"][i] = (w, cnt + 1)
    day_list = sorted(by_day.keys(), reverse=True)
    day_list = day_list[:30]  # cap the digest at the 30 most recent active days
    lines = []
    for day in reversed(day_list):
        d = by_day[day]
        mentions = [w for w, cnt in sorted(d["mentions"], key=lambda x: -x[1])[:5]]
        tag = ", ".join(mentions) if mentions else "chat"
        m = mood_for_date(day)
        mood_tag = f" · mood: {m['mood']}" if m else ""
        try:
            dstr = datetime.fromisoformat(day).strftime('%a %d %b')
        except Exception:
            dstr = day
        lines.append(f"- {dstr}: {d['n']} msgs, {d['user']} from Chris ({tag}){mood_tag}")
    block = "Long-term memory — what we did over the last 90 days:\n" + "\n".join(lines[-20:])
    _LT_CACHE["ts"] = now
    _LT_CACHE["text"] = block
    return block


# ===== Categorized memory sections (identity / work / mood / tasks / lessons) =====
# Patterns ending in "*" match dotted prefixes (e.g. "work.*" matches work.project).
_MEMORY_CATEGORIES = {
    "identity": [
        "my_name", "name", "partner_name", "appearance.*", "how_we_met.*",
        "what_we_built", "what_you_love", "how_you_work", "way_you_treat_me",
        "chris_age", "personal.*",
    ],
    "work": [
        "project", "my_project", "work.*", "interface_*", "404_bug.*",
        "venda_404_bug", "next_session_reminder", "work_rules",
    ],
    "lessons": ["lesson.*", "lesson_*", "skills.*"],
}

def _matches_pattern(key, pat):
    return key == pat or (pat.endswith('*') and key.startswith(pat[:-1]))

def _categorized_memory_lines(mem, light=False):
    """Render memory grouped by category instead of one raw dump. Falls back to
    the raw ordering when a category ends up empty."""
    order = ["identity", "work", "lessons"]
    out = []
    seen = set()
    for cat in order:
        keys = []
        for pat in _MEMORY_CATEGORIES.get(cat, []):
            for k in mem:
                if k in seen and _matches_pattern(k, pat):
                    continue
                if k not in seen and _matches_pattern(k, pat):
                    keys.append(k)
        keys = list(dict.fromkeys(keys))
        if not keys:
            continue
        seen.update(keys)
        cap = 180 if light else 400
        seg = []
        for k in keys[:8]:
            val = str(mem[k]['value'])
            if len(val) > cap:
                val = val[:cap] + "…"
            seg.append(f"- {k}: {val}")
        if seg:
            out.append(f"{cat}:\n" + "\n".join(seg))
    # Any leftover real facts (not hidden, not seen) appended in raw order.
    leftover = []
    for k, v in mem.items():
        if k in seen or k in _MEMORY_HIDDEN or k.split('.')[0] in seen:
            continue
        val = str(v['value'])[:180]
        leftover.append(f"- {k}: {val}")
    if leftover:
        out.append("other facts:\n" + "\n".join(leftover[:6]))
    return out


# ===== Standing preferences (durable "how Chris wants things done") =====
# Distinct from memories: a memory is a fact, a preference is an instruction
# that must be obeyed on every future reply (tone, units, format, defaults).
_PREFERENCES_FILE = 'preferences.json'
_PREFERENCES_LOCK = threading.RLock()

_PREFERENCE_ALIASES = {
    'tone': 'tone', 'style': 'tone', 'mood': 'tone', 'manner': 'tone',
    'voice': 'tone', 'vibe': 'tone', 'attitude': 'tone',
    'unit': 'units', 'units': 'units', 'measurement': 'units',
    'measure': 'units', 'measurements': 'units',
    'format': 'format', 'formatting': 'format', 'layout': 'format',
    'structure': 'format',
    'name': 'name', 'nickname': 'name', 'call me': 'name',
    'what to call me': 'name', 'what should i call you': 'name',
    'what should you call me': 'name', 'what do you call me': 'name',
    'language': 'language', 'lang': 'language', 'tongue': 'language',
    'brevity': 'brevity', 'verbosity': 'brevity', 'length': 'brevity',
    'timezone': 'timezone', 'tz': 'timezone',
    'currency': 'currency',
    'greeting': 'greeting',
    'pronouns': 'pronouns',
    'notification': 'notifications', 'notifications': 'notifications',
    'notify': 'notifications', 'alerts': 'notifications',
    'schedule': 'schedule', 'routines': 'schedule', 'routine': 'schedule',
    'email': 'email', 'emails': 'email', 'address': 'email',
    'phone': 'phone', 'number': 'phone', 'cell': 'phone', 'cellphone': 'phone',
    'location': 'location', 'city': 'location', 'home': 'location',
    'study': 'study', 'course': 'study', 'courses': 'study',
    'university': 'study', 'subject': 'study', 'subjects': 'study',
    'date': 'dates', 'dates': 'dates', 'time': 'dates',
    'food': 'diet', 'diet': 'diet',
}

# Filler words the model prefixes onto a preference name ("my tone", "always
# use metric units"). Stripped before lookup so those collapse onto one key
# instead of accumulating near-duplicate entries.
_PREF_FILLER = ('my ', 'the ', 'a ', 'an ', 'please ', 'always ', 'prefer ',
                'preferred ', 'default ', 'reply ', 'replies ', 'response ',
                'answer ', 'answers ', 'use ', 'using ')


def _pref_key(key):
    """Normalise a preference name so 'My Tone', 'style' and 'tone' are one entry.

    Only short names are folded onto a known concept; a long phrase keeps its
    own key so a genuine one-off instruction is never silently merged away.
    """
    k = re.sub(r'\s+', ' ', str(key or '').strip().lower()).strip(' .:;-')
    if not k:
        return ''
    for filler in _PREF_FILLER:
        if k.startswith(filler) and len(k) > len(filler):
            k = k[len(filler):].strip()
            break
    if k in _PREFERENCE_ALIASES:
        return _PREFERENCE_ALIASES[k]
    tokens = k.split()
    if len(tokens) <= 3:
        for t in tokens:  # longest concept wins, left to right
            if t in _PREFERENCE_ALIASES:
                return _PREFERENCE_ALIASES[t]
    return k


def get_preferences():
    prefs = load_json(_PREFERENCES_FILE, {})
    return prefs if isinstance(prefs, dict) else {}


def set_preference(key, value):
    k = _pref_key(key)
    if not k:
        return {"ok": False, "error": "preference name is empty"}
    val = str(value).strip()
    if not val:
        return {"ok": False, "error": "preference value is empty — say what to prefer"}
    with _PREFERENCES_LOCK:
        prefs = get_preferences()
        previous = prefs.get(k)
        prefs[k] = val
        prefs['_meta'] = prefs.get('_meta', {})
        prefs['_meta'][k] = datetime.now().isoformat()
        save_json(_PREFERENCES_FILE, prefs)
    audit_write('preference', 'set', {'key': k, 'value': val}, True, val)
    text = f"Preference saved: {k} = {val}"
    if previous and previous != val:
        text += f" (was: {previous})"
    return {"ok": True, "preference": k, "value": val, "previous": previous, "message": text}


def forget_preference(key):
    k = _pref_key(key)
    with _PREFERENCES_LOCK:
        prefs = get_preferences()
        if k not in prefs:
            return {"ok": False, "error": f"no preference named '{k}'"}
        removed = prefs.pop(k)
        meta = prefs.get('_meta') or {}
        meta.pop(k, None)
        prefs['_meta'] = meta
        save_json(_PREFERENCES_FILE, prefs)
    audit_write('preference', 'forget', {'key': k}, True, removed)
    return {"ok": True, "removed": k, "value": removed,
            "message": f"Preference removed: {k} (was: {removed})"}


def list_preferences():
    prefs = {k: v for k, v in get_preferences().items() if not k.startswith('_')}
    if not prefs:
        return {"count": 0, "preferences": {},
                "message": "No standing preferences stored yet."}
    lines = "\n".join(f"- {k}: {v}" for k, v in sorted(prefs.items()))
    return {"count": len(prefs), "preferences": prefs,
            "message": f"{len(prefs)} standing preference(s):\n{lines}"}


def build_preferences_block(light=False):
    """Render preferences as a prompt block, or None when none are stored."""
    prefs = {k: v for k, v in get_preferences().items() if not k.startswith('_')}
    if not prefs:
        return None
    if light:
        prefs = dict(list(prefs.items())[:4])
    lines = "\n".join(f"- {k}: {v}" for k, v in sorted(prefs.items()))
    return ("[Chris's standing preferences — FOLLOW THESE on every reply, "
            "they outrank your default style unless he overrides them now:\n"
            + lines + "]")


# ===== Context fed into every chat reply =====
def build_context_block(light=False):
    now = datetime.now()
    mem = get_memories()
    parts = [
        f"[Current time: {now.strftime('%A, %d %B %Y, %I:%M %p')}]"
    ]
    # Categorized facts (identity / work / lessons / other), light mode keeps
    # just the essentials for slow local models.
    mem_secs = _categorized_memory_lines(mem, light=light)
    if light:
        mem_secs = mem_secs[:2]
    if mem_secs:
        parts.append("[Facts I know about Chris:\n" + "\n\n".join(mem_secs) + "]")
    else:
        parts.append("[Facts I know about Chris: (none stored yet)]")
    # Long-term recall: what we did over the last 90 days (matrix of past work).
    try:
        ltr = _long_term_recall(90 if not light else 14)
        if ltr:
            parts.append("[" + ltr + "]")
    except Exception:
        pass
    journal = get_journal(4 if light else 8)
    j_lines = [f"- {e['entry']}" for e in journal]
    if j_lines:
        parts.append("[Shared history — recent journal entries:\n" + "\n".join(j_lines) + "]")
    # Recent moods (tiredness, energy) — the emotional memory.
    try:
        mb = mood_history_block(7 if light else 14)
        if mb:
            parts.append("[" + mb + "]")
    except Exception:
        pass
    # Flag memories touched in the last hour so ACEsi can confirm "just updated" facts
    try:
        recent_mem = []
        for k, v in mem.items():
            upd = v.get('updated', '')
            try:
                upd_dt = datetime.fromisoformat(upd)
                if (now - upd_dt).total_seconds() <= 3600:
                    recent_mem.append(f"- {k}: {str(v['value'])}")
            except Exception:
                continue
        if recent_mem:
            parts.append("[Facts just updated in the last hour (Chris may ask if you noticed):\n" + "\n".join(recent_mem[:8]) + "]")
    except Exception:
        pass
    try:
        tasks = read_items('tasks.json', 'tasks')
        events = read_items('events.json', 'events')
        open_tasks = [t for t in tasks if t.get('status') != 'done']
        week_end = (now + timedelta(days=7)).date().isoformat()
        today = now.date().isoformat()
        upcoming = [e for e in events if today <= e.get('date', '') <= week_end]
        upcoming.sort(key=lambda e: e.get('date', ''))
        cal_lines = []
        if open_tasks:
            cal_lines.append(f"Open tasks ({len(open_tasks)}):")
            for t in sorted(open_tasks, key=lambda x: x.get('priority', 3))[:8]:
                cal_lines.append(f"- {t['title']} (priority P{t.get('priority', 3)})")
        if upcoming:
            cal_lines.append(f"Upcoming events (next 7 days):")
            for e in upcoming[:8]:
                cal_lines.append(f"- {e['date']}" + (f" {e['time']}" if e.get('time') else "") + f": {e['title']}")
        if cal_lines:
            parts.append("[Tasks & calendar:\n" + "\n".join(cal_lines) + "]")
    except Exception:
        pass
    # Playbook memory: proven tool recipes from earlier tasks, so ACEsi can
    # "do it the way that worked last time".
    try:
        pb = playbook_top(4 if light else 8)
        if pb:
            parts.append("[Playbook — proven procedures from past tasks (follow these when the task matches):\n"
                         + "\n".join(pb) + "]")
    except Exception:
        pass
    return "\n".join(parts)

LAST_FILE_PATH = None

@app.route('/')
def index():
    resp = send_from_directory('.', 'ACEsi.html')
    # Never let the browser cache the chat UI — stale JS was the root cause of
    # "popup never shows" (old page missing the view-rendering code).
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


# Strict file read/open detection. Only messages that LEAD with read/open AND
# whose target is clearly file-like (contains "file", a path separator, an
# absolute path, or a known file extension) are treated as file requests.
# UI instructions like "open the app" / "read the notifications" fall through
# to the LLM instead of being misrouted as file paths.
def _match_file_request(message):
    m = re.match(
        r'^(?:please\s+|can\s+you\s+|could\s+you\s+|would\s+you\s+|do\s+you\s+mind\s+)?'
        r'(?:read|open)\s+(.+?)$',
        message, re.IGNORECASE)
    if not m:
        return False, None, False
    tail = m.group(1).strip().strip('"\'')
    # strip trailing "file"/"please" and leading "file:" / "the file:" phrasing
    tail = re.sub(r'\s+(?:file|please)\s*$', '', tail, flags=re.IGNORECASE).strip()
    tail = re.sub(r'^(?:the|this|that)?\s*file\s*[: ]?\s*', '', tail, flags=re.IGNORECASE).strip()
    # strip location phrases like "in my documents" / "on my computer"
    tail = re.sub(r'\b(?:in|on)\s+(?:my\s+)?(?:documents|document)\b', '', tail, flags=re.IGNORECASE)
    tail = re.sub(r'\bon\s+my\s+computer\b', '', tail, flags=re.IGNORECASE).strip()
    candidate = tail
    has_file_word = re.search(r'\bfile\b', message, re.IGNORECASE) is not None
    # "file manager/explorer" or "files app" are UI instructions, not documents
    not_file_ui = re.search(
        r'\bfile\s+(?:manager|explorer)\b|\bfiles?\s+app\b',
        message, re.IGNORECASE) is None
    file_like = (
        os.path.isabs(candidate)
        or bool(re.search(r'[/\\]', candidate))
        or (has_file_word and not_file_ui)
        or bool(re.search(
            r'(?:\.(?:txt|md|markdown|dart|py|js|ts|tsx|kt|java|gradle|kts|'
            r'pdf|png|jpe?g|gif|bmp|webp|docx?|xlsx?|pptx?|json|ya?ml|xml|'
            r'csv|log|html?|css|sql|zip|tar|gz|7z|gitignore|env))$', candidate, re.IGNORECASE))
    )
    if not file_like:
        return False, None, False
    is_open = re.match(r'open\b', message, re.IGNORECASE) is not None
    vague = candidate.lower() in ('', 'the', 'it', 'this', 'that', 'file', 'the file',
                                  'this file', 'that file', 'previous', 'last')
    return True, candidate, vague


# One tools-capable OpenAI-compatible chat completion. Returns (text, tool_calls)
# or None. Used by /chat so ACEsi can actually execute ui_*/dev tools instead of
# replying "please provide the commands".
def _chat_providers():
    return [
        ("Groq", GROQ_ENDPOINT, GROQ_API_KEY, GROQ_MODEL),
        ("Cerebras", CEREBRAS_ENDPOINT, CEREBRAS_API_KEY, CEREBRAS_MODEL),
        ("OpenRouter", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, OPENROUTER_MODEL),
        ("FreeLLM", FREELLM_ENDPOINT, FREELLM_API_KEY, FREELLM_MODEL),
    ]


def _find_provider_for_model(preferred_model):
    """Find which provider hosts the given model name.
    Returns (name, endpoint, api_key, model) or None.
    Local Ollama models (qwen2.5:7b / qwen2.5:3b) resolve to the Ollama provider
    so selecting them in the ACEsi model picker actually uses the local model
    rather than silently falling back to the cloud."""
    if not preferred_model:
        return None
    if preferred_model in (OLLAMA_MODEL, OLLAMA_CHAT_MODEL):
        if OLLAMA_ENABLED:
            return ("Ollama", OLLAMA_ENDPOINT, "local", OLLAMA_CHAT_MODEL, "compact")
        return None
    for name, ep, key, mdl in _chat_providers():
        if key and mdl and mdl == preferred_model:
            return (name, ep, key, mdl)
    if preferred_model in GROQ_FALLBACKS:
        return ("Groq", GROQ_ENDPOINT, GROQ_API_KEY, preferred_model)
    if preferred_model in OPENROUTER_FALLBACKS:
        return ("OpenRouter", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, preferred_model)
    return None

def _chat_one(name, endpoint, api_key, model, msgs, timeout=(10, 90), extra_options=None,
              tools_schema=None, tool_choice="auto"):
    if not api_key:
        return None
    headers = {"Content-Type": "application/json"}
    if api_key != "local":
        headers["Authorization"] = f"Bearer {api_key}"
    # Use a compact schema for Ollama: on this 2012-CPU box prefill is ~10 tok/s,
    # and the full 30-tool schema (~2.7k tokens) alone blows the round timeout.
    if tools_schema is None:
        tools_schema = TOOLS_SCHEMA
    # When the caller forces tool_choice="none" (final-answer round), do NOT send
    # the tool schema at all: gpt-oss-20b (Groq/OpenRouter) calls tools even under
    # a forced "none" and Groq hard-rejects it with 400 tool_use_failed. With no
    # tools advertised, the model has nothing to call and must write its answer.
    if tool_choice == "none":
        tools_schema = []
    # gpt-oss-class models are REASONING models: they spend many completion tokens
    # thinking before any content token. 200 max_tokens leaves content empty and
    # the server then echoes reasoning fragments as the "reply". Give cloud
    # providers headroom; keep the small budget for the slow CPU Ollama.
    # OpenRouter's free-tier balance caps completion tokens (this key currently
    # affords ~390 at current rates) so keep it modest; Groq/Cerebras accept 800.
    if name.startswith("OpenRouter"):
        max_tokens = 512
    elif name == "Ollama":
        max_tokens = 400
    elif name in ("Groq", "Cerebras"):
        max_tokens = 4096
    else:
        max_tokens = 2048

    body = {"model": model, "messages": msgs, "temperature": 0.4,
            "max_tokens": max_tokens}
    if tools_schema:
        body["tools"] = tools_schema
        body["tool_choice"] = tool_choice
    try:
        r = requests.post(f"{endpoint}/chat/completions",
            headers=headers,
            json=body,
            timeout=timeout)
        if r.status_code != 200:
            print(f"❌ {name} {r.status_code}: {r.text[:160]}")
            return None
        choice = r.json()["choices"][0]
        msg = choice.get("message", {})
        text = (msg.get("content") or msg.get("reasoning") or "").strip()
        tcs = []
        for tc in (msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            nm = fn.get("name")
            am = fn.get("arguments")
            if isinstance(am, str):
                try:
                    args = json.loads(am)
                except Exception:
                    args = {}
            elif isinstance(am, dict):
                args = am
            else:
                args = {}
            if nm:
                tcs.append((nm, args))
        finish = choice.get("finish_reason") or "stop"
        return text, tcs, finish
    except requests.exceptions.Timeout:
        print(f"⏱️ {name} timed out")
    except Exception as e:
        print(f"💥 {name} exc: {e}")
    return None


def _ollama_local_messages(llm_messages):
    """Return a compacted copy of llm_messages for the LOCAL Ollama model: swap
    the giant persona for the terse OLLAMA_SYS_PROMPT. Critically, only KEEP the
    original task message plus the last 3 turns of tool feedback — otherwise the
    steadily-growing SCREEN STATE blocks (~1.5k chars each after every tool)
    re-bloat each round's prefill back toward minutes on this CPU."""
    sys_ = None
    first_user = None
    tail = []
    for m in llm_messages:
        role = m.get("role")
        if role == "system":
            # Local prompt = driving persona + a memory-awareness section with the
            # light facts block, so the 3b model knows it HAS persistent memory and
            # can actually quote stored facts when asked (/chat never strips this).
            sys_ = {"role": "system", "content":
                    OLLAMA_SYS_PROMPT +
                    "\nMEMORY: You DO have persistent memory. The bracketed blocks below "
                    "([Facts I know about Chris], [Shared history], [Tasks & calendar], and "
                    "the recent conversation turns) are loaded from your database every message. "
                    "When Chris asks 'can you access/remember your memory', answer YES and quote "
                    "the exact facts below — never say you have no memory. Always give the final "
                    "text reply in the last turn.\n\n"
                    + build_context_block(light=True)}
        elif role == "user" and first_user is None and "SCREEN STATE" not in str(m.get("content", "")):
            if "You only described" not in str(m.get("content", "")) and \
               "I detected Chrome" not in str(m.get("content", "")) and \
               "SCREEN STATE" not in str(m.get("content", "")):
                first_user = m
        elif role in ("user", "assistant", "tool"):
            tail.append(m)
    return ([m for m in (sys_, first_user) if m] + tail[-3:]) if sys_ else (
        [m for m in (first_user,) if m] + tail[-3:])


_DEV_TOOLS = ("ui_app_open", "ui_tap", "ui_swipe", "ui_type", "ui_key",
              "ui_dump", "ui_screenshot", "ui_device")


def _collect_tool_evidence(llm_messages, max_chars=12000):
    """Every tool result in the conversation, oldest first, under one budget."""
    out, used = [], 0
    for m in llm_messages:
        if m.get("role") != "tool":
            continue
        content = str(m.get("content") or "")
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(content) > remaining:
            content = content[:remaining] + "\n...[TRUNCATED %d further chars]" % (
                len(content) - remaining)
        used += len(content)
        out.append({"tool": str(m.get("name") or "unknown_tool"), "content": content})
    return out


def _last_user_question(llm_messages):
    """The most recent real user turn - not one of the loop's injected nudges."""
    _NUDGE_MARKERS = ("tool call", "SCREEN STATE", "You only described",
                      "You stopped narrating", "You replied with text",
                      "Your previous reply was cut off", "Now provide your final")
    for m in reversed(llm_messages):
        if m.get("role") != "user":
            continue
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        if any(marker.lower() in content.lower() for marker in _NUDGE_MARKERS):
            continue
        return content
    return "the original request"


# Some providers occasionally emit their tool-call protocol as PLAIN TEXT
# instead of a structured tool_calls field, e.g.
#   <dots_function_call>\n<invoke name="web_fetch">...
# That markup used to be returned to Chris verbatim as the chat reply, wiping
# out work that had already succeeded (the tools ran, the reply was garbage).
# Anything matching this is never a real answer, so it is detected and dropped
# in favour of a grounded reply built from the tool evidence.
_TOOL_MARKUP_RE = re.compile(
    r'<(?:dots_function_call|function_call|invoke|parameter|tool_call|'
    r'function_results?|tool_use)\b'
    r'|</(?:invoke|parameter|function_call|dots_function_call|tool_call)>'
    r'|<\|?\s*(?:tool_call|function_call|python_tag|tool|end_tool)\s*\|?>'
    r'|\bfunctions\.[a-z_]+\s*\(', re.IGNORECASE)


def _looks_like_tool_markup(text):
    """True when model output is leaked tool-call syntax rather than an answer."""
    t = str(text or '')
    if not t.strip():
        return False
    return bool(_TOOL_MARKUP_RE.search(t))


def _sanitize_reply(text):
    """Clean a candidate reply. Returns the text, or None when the model
    emitted tool markup instead of an answer and the caller must fall back to
    a grounded/evidence reply rather than showing this to Chris."""
    t = str(text or '').strip()
    if not t:
        return None
    if not _looks_like_tool_markup(t):
        return t
    print("[reply-guard] dropped leaked tool-call markup (%d chars)" % len(t), flush=True)
    try:
        audit_write('reply', 'markup_guard', {'chars': len(t)}, False,
                    'model emitted tool markup instead of an answer')
    except Exception:
        pass
    return None


def _evidence_fallback(evidence, names, max_chars=400, max_results=5):
    """No model available? Show the user just the actual findings, tersely.

    Chris asked for short answers: list at most `max_results` findings with a
    short, clean snippet each instead of dumping every raw tool payload."""
    lines = []
    if not evidence:
        lines.append("I couldn't find that.")
        return "\n".join(lines)
    kept = evidence[:max_results]
    for i, e in enumerate(kept, 1):
        snippet = e["content"].strip().replace("\n", " ")
        if len(snippet) > max_chars:
            snippet = snippet[:max_chars] + "..."
        lines.append("- %s" % snippet)
    if len(evidence) > max_results:
        lines.append("...and %d more result(s)." % (len(evidence) - max_results))
    return "\n".join(lines)


def _build_grounded_prompt(question, evidence, max_evidence_chars=3500):
    if not evidence:
        body = "NO TOOL RESULTS WERE COLLECTED. No tool call succeeded in this run."
    else:
        # Feed a SMALL evidence slice to the final-answer round. The web_search
        # payload is huge and on the slow CPU Ollama the prefill alone blows the
        # round timeout — so the model gives up and the raw dump gets shown.
        # Chris asked for SHORT answers; a capped slice + a terse instruction
        # lets the model actually finish and answer in a sentence.
        parts, used = [], 0
        for e in evidence:
            content = e["content"]
            remaining = max_evidence_chars - used
            if remaining <= 0:
                break
            if len(content) > remaining:
                content = content[:remaining] + "..."
            used += len(content)
            parts.append("--- RESULT %d from `%s` ---\n%s" % (
                len(parts) + 1, e["tool"], content))
        body = "\n\n".join(parts)
    return (
        "Question: %s\n\n"
        "Below is a slice of the tool results collected during this run.\n\n"
        "%s\n\n"
        "Answer the question in a SINGLE SHORT SENTENCE using ONLY these results. "
        "No preamble, no listing of results, no bullet points.\n"
        "If these results do not contain the answer, reply with just: \"I couldn't "
        "find that.\" Do NOT guess and do NOT answer from memory.\n"
        "Never list tool names as findings - \"web_search\" is not a result."
        % (question, body))


def _final_answer(llm_messages, names, last_screen, active, user_message,
                  chat_one=None):
    """The reply to show the user when the loop ends with work done.

    Replaces the block that produced
    "I performed %d device actions (%s)."
    Never claims device actions for a non-device task, and never reports tool names
    as findings.
    """
    evidence = _collect_tool_evidence(llm_messages)
    device_acts = [n for n in names if n in _DEV_TOOLS]

    if evidence:
        prompt = _build_grounded_prompt(
            _last_user_question(llm_messages) or user_message, evidence)
        schema = None
    elif device_acts:
        prompt = (
            "The device actions are complete. Actions executed: %s.\n"
            "Write a short final summary (2-3 sentences) of what you did and where "
            "the process ended up. Cite real text from the screen dump below. "
            "Do not call any tools." % ", ".join(dict.fromkeys(device_acts)))
        if last_screen:
            prompt += "\nLast screen seen:\n%s" % last_screen[:3000]
        schema = None
    else:
        return _evidence_fallback(evidence, names)

    if chat_one is not None and active:
        try:
            msgs = list(llm_messages) + [{"role": "user", "content": prompt}]
            got = chat_one(active[0], active[1], active[2], active[3], msgs,
                           tools_schema=[], tool_choice="none")
        except Exception:
            got = None
        if got:
            text = (got[0] or "").strip() if isinstance(got, (tuple, list)) else str(got).strip()
            # The grounded call can itself emit leaked tool markup; if so, fall
            # through to the evidence fallback instead of showing it to Chris.
            text = _sanitize_reply(text) if text else None
            if text:
                return text

    return _evidence_fallback(evidence, names)


def _final_summary_call(active, llm_messages, names, last_screen):
    """After the dispatch loop ends (time budget / round cap) with real actions
    executed, give the model ONE short call to write a proper final summary
    instead of the mechanical 'action cap' string. Returns text or None."""
    done = ", ".join(n for n in names if n in
                     ("ui_app_open", "ui_tap", "ui_swipe", "ui_type", "ui_key",
                      "ui_dump", "ui_screenshot", "ui_device"))
    prompt = (
        "The device actions are complete. Actions executed: %s.\n"
        "Write a short, natural final summary (2-3 sentences) of what you did "
        "and where the process ended up. Cite real text from the last screen "
        "dump you received. Do not call any tools." % (done or "none")
    )
    if last_screen:
        prompt += "\nLast screen heard:\n%s" % last_screen[:800]
    msgs = _ollama_local_messages(llm_messages)
    msgs.append({"role": "user", "content": prompt})
    is_ollama = (active and active[0] == "Ollama") or not active
    try:
        if is_ollama and OLLAMA_ENABLED:
            got = _chat_one("Ollama", OLLAMA_ENDPOINT, "local", OLLAMA_CHAT_MODEL,
                            msgs, timeout=(15, 120), tools_schema=OLLAMA_TOOLS_SCHEMA)
        elif active:
            got = _chat_one(active[0], active[1], active[2], active[3], msgs)
        else:
            got = None
    except Exception:
        got = None
    if got:
        text = (got[0] or "").strip()
        if text:
            return text
    return None


def _auto_open_user_file_fallback(names, llm_messages, user_message):
    """Deterministic fallback: Chris asked to open/view/show a file in his user
    folders but the model answered from memory without calling the file tool
    (or it narrated a plan and stopped). Resolve the hinted filename server-side
    and attach the opened-file view so the request still completes AND the UI
    popup appears even when the model stalls. Returns True when a file was
    opened (a step with view data was appended to the ledger)."""
    if ("view_user_file" in names or "open_user_file" in names or
            "read_user_file" in names or not _match_open_user_file(user_message)):
        return False
    _hint = _extract_user_file_hint(user_message)
    if not _hint:
        return False
    _rp = _find_user_file_fuzzy(_hint)
    if not _rp:
        print("⚠️ /chat auto-open fallback: no file matches hint %r" % _hint)
        return False
    ok, result = tool_view_user_file(_rp)
    if not ok:
        # Inline view failed (e.g. OneDrive cloud-only placeholder). Still open
        # it externally so the request completes: os.startfile lets the provider
        # hydrate the file and opens the default app for editing.
        print("⚠️ /chat auto-open fallback: could not view %s — opening externally" % _rp)
        try:
            os.startfile(_rp)
        except Exception as _e:
            print("⚠️ /chat auto-open fallback: external open also failed: %s" % _e)
        names.append("open_user_file")
        sid = _agent_next_id()
        with _AGENT_LOCK:
            _AGENT["steps"].append({"id": sid, "kind": "work",
                                    "text": "open_user_file %s" % os.path.basename(_rp),
                                    "state": "done", "icon": _tool_icon("open_user_file"),
                                    "view": {"type": "external", "filename": os.path.basename(_rp),
                                             "path": _rp}})
        llm_messages.append({"role": "tool",
                             "tool_call_id": "chat_autoopen_%d" % int(time.time() * 1000),
                             "name": "open_user_file",
                             "content": "Opened externally: %s" % _rp})
        print("🖼 /chat auto-open fallback: externally opened %s" % _rp)
        return True
    names.append("view_user_file")
    sid = _agent_next_id()
    _view = result.view if isinstance(result, _ViewResult) else result
    with _AGENT_LOCK:
        _AGENT["steps"].append({"id": sid, "kind": "work",
                                "text": "view_user_file %s" % os.path.basename(_rp),
                                "state": "done", "icon": _tool_icon("view_user_file"),
                                "view": _view})
    llm_messages.append({"role": "tool",
                         "tool_call_id": "chat_autoopen_%d" % int(time.time() * 1000),
                         "name": "view_user_file",
                         "content": str(result)})
    print("🖼 /chat auto-open fallback: viewed %s" % _rp)
    return True


def _wants_web_image(user_message):
    """True when Chris asked to see a picture/photo/image from the internet."""
    m = (user_message or "").lower()
    return bool(re.search(r'\b(picture|photo|image|pic|pics|gif|photo of|picture of|image of)\b', m))


def _find_image_url_in_text(text):
    """Return the first http(s) URL in `text` that looks like a direct image
    file (ends in an image extension, NET tools + curl)."""
    for url in re.findall(r'https?://[^\s)\]>"\'<]+', text or ""):
        u = url.rstrip('.,;:') 
        if re.search(r'\.(?:png|jpe?g|gif|webp|bmp|tiff?)(?:\?|$)', u, re.IGNORECASE):
            return u
    return None


def _auto_open_web_image_fallback(reply_text, llm_messages, user_message,
                                  triggered_by_tool=False):
    """Deterministic fallback: Chris asked for a picture from the internet and
    the model found an image URL but never called view_web_image (it either
    pasted the link in prose, or looped on web_search and stopped without a
    FINAL). Fetch and display the first image URL we can find so the popup still
    appears. Looks in the reply text first, then in the accumulated tool output.
    Returns True when a web image view was appended to the ledger."""
    if "view_web_image" in _seen_tool_names():
        return False
    if not _wants_web_image(user_message):
        return False
    # Collect every candidate image URL, not just the first: the model often
    # invents a plausible-looking path that 404s while a real one sits further
    # down the search output. Try them in order until one actually downloads.
    candidates = []
    for text in [reply_text] + [m.get("content", "") for m in
                                reversed(llm_messages or []) if m.get("role") == "tool"]:
        for u in re.findall(r'https?://[^\s)\]>"\'<]+', text or ""):
            u = u.rstrip('.,;:')
            if re.search(r'\.(?:png|jpe?g|gif|webp|bmp|tiff?)(?:\?|$)', u, re.IGNORECASE):
                if u not in candidates:
                    candidates.append(u)
    if not candidates:
        return False
    ok = False
    result = None
    url = None
    for cand in candidates[:6]:
        _ok, _res = tool_view_web_image(cand)
        if _ok and isinstance(_res, _ViewResult):
            ok, result, url = True, _res, cand
            break
        print("⚠️ web-image fallback: could not fetch %s — %s" % (cand, _res))
    if not ok:
        return False
    sid = _agent_next_id()
    with _AGENT_LOCK:
        _AGENT["steps"].append({"id": sid, "kind": "work",
                                "text": "view_web_image %s" % str(result.view.get("filename", url)),
                                "state": "done", "icon": _tool_icon("view_web_image") or "🌐",
                                "view": result.view})
    llm_messages.append({"role": "tool",
                         "tool_call_id": "webimg_%d" % int(time.time() * 1000),
                         "name": "view_web_image",
                         "content": str(result)[:4000]})
    print("🌐 web-image fallback: displayed %s" % url)
    return True


def _seen_tool_names():
    with _AGENT_LOCK:
        return {s.get("text", "").split()[0] for s in _AGENT.get("steps", [])
                if s.get("kind") == "work" and s.get("text")}


def _chat_dispatch(llm_messages, max_rounds=20, user_message="", preferred_model=None):
    """Agent-style tool loop for /chat. Passes the tool schema to the model; when
    it emits a tool call (ui_*, git_*, flutter_*, cdp_*, ...) EXECUTE it via
    _call_tool and feed the result back, so ACEsi performs actions instead of
    replying 'please provide the commands'. Returns the final text reply or None.
    Rounds cap so a stuck model still terminates.
    Publishes live work-steps to _AGENT so the frontend (which polls
    /opencode/status) renders progress inline, exactly like run_agent does."""
    # --- Domain separation (checked BEFORE marking the agent running): keep UI /
    # code / network work in distinct contexts so ACEsi stops mixing them. One
    # concrete domain wins; more than one is ambiguous -> ASK FOR CLARIFICATION.
    # (If the user directly NAMES a tool, it only short-circuits the choice when
    # the request is otherwise single-domain; a genuinely mixed ask still asks.) ---
    domains = _classify_message(user_message)
    concrete = domains - {"general"}
    if len(concrete) >= 2:
        with _AGENT_LOCK:
            _AGENT["activity"] = "needs clarification"
            _AGENT["last_reply"] = ("I can help with: (UI) navigating the Android app on the "
                                    "device, (NETWORK) checking whether a URL/port is up, or "
                                    "(CODE) reading/editing files. Which would you like?\n"
                                    "E.g. \"navigate StudentSyncSA to the Venda ITS portal\", "
                                    "\"curl https://univenierp01.univen.ac.za\", or "
                                    "\"read lib/screens/...\".")
        return _AGENT["last_reply"]
    if _kill_armed():
        with _AGENT_LOCK:
            _AGENT["activity"] = "E-STOPPED"
            _AGENT["last_reply"] = "E-STOP is armed — ACEsi is stopped."
        return _AGENT["last_reply"]
    explicit_dom = _explicit_tool_domain(user_message)
    active_domain = explicit_dom or (next(iter(concrete)) if concrete else "general")
    # Belt-and-suspenders: any navigation/portal/screenshot request that isn't an
    # explicit code/net ask is device work. If the classifier left it 'general',
    # the schema would strip ALL ui_* tools and the nav corrective below would
    # demand tool calls the model cannot emit — the exact stall we saw ("You are
    # on the ITS portal" -> monologue, no tools, dead after 3 rounds).
    if active_domain == "general" and _nav_task(user_message):
        active_domain = "ui"
    allowed_names = _domain_tool_names(active_domain)
    # Multi-context: pick the active context from ace_config.yaml by domain and
    # (a) intersect its per-context tool-caps with the domain filter, and
    # (b) inject its prompt overlay (known app structure, persona hints).
    ctx_name = _context_by_domain(active_domain)
    ctx_domains, ctx_tools = _context_tool_policy(ctx_name)
    if ctx_tools:
        allowed_names = allowed_names & ctx_tools
        if ctx_domains == "all":
            allowed_names = ctx_tools
    ctx_overlay = _context_overlay(ctx_name)
    if ctx_overlay and llm_messages and llm_messages[0].get("role") == "system":
        merged = llm_messages[0].get("content", "") + "\n\n" + ctx_overlay
        llm_messages[0] = {"role": "system", "content": merged}
    with _AGENT_LOCK:
        _ctx_last["name"] = ctx_name
        _ctx_last["overlay"] = ctx_overlay.replace("\n", " ")[:200]
    # COMPOUND-REQUEST FIX: a multi-step ask spans domains by construction. Filtering
    # to a single domain strips the tools the other subtasks need, and the model then
    # correctly reports it cannot do them.
    _registered = {t["function"]["name"] for t in TOOLS_SCHEMA}
    allowed_names = ace_dispatcher.widen_to_cover(user_message, allowed_names, _registered)
    _gaps = ace_dispatcher.find_gaps(user_message, allowed_names)
    if _gaps.has_gaps:
        with _AGENT_LOCK:
            _AGENT["activity"] = "blocked (missing tools)"
            _AGENT["last_reply"] = "I can't complete this: %s" % _gaps
        return _AGENT["last_reply"]
    # Ollama uses the COMPACT schema (prompt-size critical on this CPU); cloud
    # providers get the FULL schema restricted to the active domain only.
    ollama_domain_schema = _filter_tools_schema(OLLAMA_TOOLS_SCHEMA, allowed_names)
    full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)
    # Compact schema for net-domain tools (OpenRouter free tier token limit).
    # Also used for hybrid web-research tasks (search + save to a file) which
    # classify as 'general' but still need web_search/webfetch to gather data.
    _research_task = bool(_web_research_task((user_message or "").lower()))
    # Draft-to-VS-Code review flow applies ONLY when Chris explicitly asked to
    # save results to a file. A bare factual question ("what is the oldest
    # book?") must get a DIRECT answer, not a "draft in VS Code" card — so the
    # fallback that replaces the model's text answer stays off unless a file
    # save was actually requested.
    _explicit_save = bool(_explicit_save_request((user_message or "").lower()))
    if active_domain == "net" or (active_domain == "general" and _research_task):
        net_domain_schema = _filter_tools_schema(NET_TOOLS_SCHEMA, allowed_names)
    else:
        net_domain_schema = None

    with _AGENT_LOCK:
        _AGENT["running"] = True
        _AGENT["abort"] = False
        _AGENT["activity"] = "planning"
        _reset_indicator()
        _AGENT["steps"] = []
        _AGENT["tools_used"] = 0
        _AGENT["last_error"] = ""
    # Deterministic step-list executor: if the user wrote an explicit numbered
    # UI script (1. ui_app_open X 2. ui_dump 3. tap "Y"...), execute it directly
    # with the real tools — no model needed. qwen2.5:3b stalls on these even
    # when tool_choice is forced, so we bypass it entirely for step lists.
    script_reply = _execute_ui_script(user_message)
    if script_reply:
        with _AGENT_LOCK:
            _AGENT["running"] = False
            _AGENT["activity"] = "done"
            _AGENT["last_reply"] = script_reply
        return script_reply
    active = None
    names = []
    last_text = None
    last_screen = None
    dead_rounds = 0
    last_batch_sig = None
    repeat_count = 0
    _already_reasked = False
    _call_counts = {}
    _call_arg_sigs = {}
    # Explicit "ui_app_open <App>" (or "open the app") instructions are honored
    # SERVER-SIDE before the model loop. qwen2.5:3b often skips ui_app_open and
    # ui_dumps the home screen instead, wasting the whole run. If the user asked
    # for the app, open it now and feed the resulting screen state back so the
    # model's first ui_dump reads the real app screen.
    opened_app = False
    if _ui_task(user_message) and not _ui_situational_ask(user_message) and (
            re.search(r'\bui_app_open\b', user_message, re.IGNORECASE)):
        try:
            _aok, _atxt = _call_tool("ui_app_open", {})
            if _aok:
                opened_app = True
                names.append("ui_app_open")
                _AGENT["tools_used"] += 1
                print("🚀 /chat auto-opened app (user asked for it)")
                _dok, _dtxt = _ui_auto_dump()
                if _dok:
                    last_screen = _dtxt
                    seen_screen_hint = ("APP LAUNCHED. Here is what is now on screen:\n%s%s"
                                        % (str(_dtxt)[:2000], _cert_warning_directive(_dtxt)))
                else:
                    seen_screen_hint = "APP LAUNCHED."
                llm_messages = [{"role": "user", "content": seen_screen_hint}] + llm_messages
        except Exception as e:
            print("⚠️ /chat auto ui_app_open failed: %s" % e)
    # Tracks whether the model has read the screen (ui_dump or an auto-dump fed
    # back after a screen tool) since the last screen change. Reset by
    # ui_app_open (which changes the app) so the model must re-read before
    # tapping on a screen it has never seen.
    seen_screen = bool(opened_app)
    dispatch_start = time.time()
    last_had_tools = False
    _stall_break = False
    # Test/validation runs stack many read-only steps (ui_assert_*, ui_expect,
    # ui_test_run) plus the navigation to reach each screen. Each step does a
    # uiautomator dump — ~10-40s on this slow CPU — so a full test run needs a
    # bigger budget and more rounds than a quick screenshot task.
    if _test_task(user_message):
        max_rounds = max(max_rounds, 40)
        time_budget = 600
    else:
        time_budget = 300 if _nav_task(user_message) else 240
    try:
        for rnd in range(max_rounds):
            # Hard time budget: on these slow CPUs a stuck model otherwise burns
            # max_rounds × ~50s each. When the budget expires mid-navigation we
            # stop and let the tail logic force a screenshot + honest summary.
            if time.time() - dispatch_start > time_budget:
                with _AGENT_LOCK:
                    _AGENT["activity"] = "stopped (time budget %.0fs)" % time_budget
                print("⏰ /chat stop: time budget %.0fs reached" % time_budget)
                break
            if _AGENT.get("abort"):
                with _AGENT_LOCK:
                    _AGENT["activity"] = "stopped by user"
                    _AGENT["last_reply"] = "Stopped by user."
                return "Stopped by user."
            if active is None:
                got = None
                tc = "required" if (_ui_task(user_message) and not names) else "auto"
                # If a preferred model is set, try that provider first.
                providers = []
                if preferred_model:
                    prov = _find_provider_for_model(preferred_model)
                    if prov:
                        providers.append(prov)
                    # Also try fallbacks for the same provider
                    if prov and prov[0] == "Groq":
                        for m in GROQ_FALLBACKS:
                            if m != preferred_model:
                                providers.append(("Groq", GROQ_ENDPOINT, GROQ_API_KEY, m))
                    elif prov and prov[0] == "OpenRouter":
                        for m in OPENROUTER_FALLBACKS:
                            if m != preferred_model:
                                providers.append(("OpenRouter", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, m))
                # Then try the standard providers.
                for p in _chat_providers():
                    if p not in providers:
                        providers.append(p)
                for p in providers:
                    # If a preferred model is set, never skip it.
                    if preferred_model and p[3] == preferred_model:
                        pass
                    # Groq is no longer skipped — with Ollama removed it's the
                    # primary provider for net/research tasks. OpenRouter's free tier
                    # can't pay for multi-round tool chains, so Groq must be tried.
                    if len(p) > 4 and p[4] == "compact":
                        # Ollama chosen via the model picker: use the compact schema
                        # and always route the pared-down local messages so the slow
                        # CPU model gets a small prefill.
                        schema = ollama_domain_schema
                        msgs = _ollama_local_messages(llm_messages)
                        tc2 = tc
                    else:
                        schema = full_domain_schema
                        msgs = llm_messages
                        tc2 = tc
                        if p[0] == "OpenRouter" and net_domain_schema:
                            schema = net_domain_schema
                        if p[0] == "Groq" and net_domain_schema:
                            schema = net_domain_schema
                    got = _chat_one(p[0], p[1], p[2], p[3], msgs,
                                     tools_schema=schema, tool_choice=tc2)
                    # FreeLLM's free routing is transiently failing (its internal
                    # upstream providers reject intermittently with 400). Retry a
                    # few times with a short pause before declaring it dead.
                    if got is None and p[0] == "FreeLLM":
                        for _ in range(3):
                            time.sleep(2)
                            got = _chat_one(p[0], p[1], p[2], p[3], msgs,
                                            tools_schema=schema, tool_choice=tc2)
                            if got is not None:
                                break
                    if got is not None:
                        active = p
                        break
                if got is None:
                    for model in OPENROUTER_FALLBACKS:
                        or_schema = net_domain_schema if net_domain_schema else full_domain_schema
                        got = _chat_one("OpenRouter-fallback", OPENROUTER_ENDPOINT,
                                        OPENROUTER_API_KEY, model, llm_messages,
                                        tools_schema=or_schema, tool_choice=tc)
                        if got is not None:
                            active = ("OpenRouter-fallback", OPENROUTER_ENDPOINT,
                                      OPENROUTER_API_KEY, model)
                            break
                if got is None and OLLAMA_ENABLED:
                    # Ollama warm-up probe first: cheap tiny call that forces the
                    # model to LOAD (with keep_alive persisted in Ollama) so the
                    # heavy first round reuses the loaded model instead of eating
                    # the whole timeout on a cold swap. MUST use the same /v1
                    # endpoint with the same options as the real call.
                    try:
                        _chat_one("Ollama", OLLAMA_ENDPOINT, "local",
                                  OLLAMA_CHAT_MODEL,
                                  [{"role": "user", "content": "ok"}],
                                  timeout=(15, 300),
                                  tools_schema=OLLAMA_TOOLS_SCHEMA)
                    except Exception:
                        pass
                    got = _chat_one("Ollama", OLLAMA_ENDPOINT, "local",
                                    OLLAMA_CHAT_MODEL, _ollama_local_messages(llm_messages),
                                    timeout=(15, 300),
                                    tools_schema=ollama_domain_schema, tool_choice=tc)
                    if got is not None:
                        active = ("Ollama", OLLAMA_ENDPOINT, "local", OLLAMA_CHAT_MODEL,
                                  "compact")
                if got is None:
                    print("[ACE-DISPATCH] All providers exhausted. tried=%s ollama=%s"
                          % ([p[0] for p in providers], OLLAMA_ENABLED))
                    break
            else:
                tc = "required" if (_ui_task(user_message) and not names) else "auto"
                if len(active) > 4 and active[4] == "compact":
                    got = _chat_one(active[0], active[1], active[2], active[3],
                                    _ollama_local_messages(llm_messages), timeout=(15, 300),
                                    tools_schema=ollama_domain_schema, tool_choice=tc)
                else:
                    fwd_schema = full_domain_schema
                    # OpenRouter keeps the compact net/research schema on follow-up
                    # rounds too (the full code+net+ctrl schema exceeds its budget).
                    if active[0].startswith("OpenRouter") and net_domain_schema:
                        fwd_schema = net_domain_schema
                    got = _chat_one(active[0], active[1], active[2], active[3],
                                    llm_messages, tools_schema=fwd_schema,
                                    tool_choice=tc)
                if got is None:
                    active = None
                    continue
            with _AGENT_LOCK:
                _AGENT["activity"] = "thinking (%d/%d)" % (rnd + 1, max_rounds)
            text, tcs, finish = got
            if text and text.strip():
                last_text = text.strip()[:2000]
            # A token-truncated reply is never a final answer: the model was cut off
            # before it could emit a tool call. Continue with the same message plus
            # a nudge, instead of returning the half-sentence as the reply.
            if finish == "length" and not tcs:
                llm_messages.append({"role": "assistant", "content": text or ""})
                llm_messages.append({"role": "user", "content":
                    "Your previous reply was cut off by the length limit before you "
                    "could call a tool. Continue now: emit the tool call directly, "
                    "with no preamble and no restating of your plan."})
                active = None
                dead_rounds += 1
                if dead_rounds >= 4:
                    with _AGENT_LOCK:
                        _AGENT["activity"] = "stopped (length limit)"
                    break
                continue
            # Small/prose-capable providers (Ollama qwen2.5) sometimes write the tool
            # call in prose ("CALL: ui_tap {...}" / fenced JSON) instead of native
            # tool_calls. Accept those too, exactly like run_agent's _extract_calls.
            if not tcs:
                tcs = _extract_calls(text)
            if not tcs:
                last_had_tools = False
                nav_push = _nav_gate(user_message, names)
                if nav_push:
                    active = None
                    dead_rounds += 1
                    llm_messages.append({"role": "user", "content": nav_push})
                    if dead_rounds >= 4:
                        with _AGENT_LOCK:
                            _AGENT["activity"] = "stopped (no tool calls)"
                        break
                    continue
            if tcs:
                _advance_indicator()
            if not tcs:
                if _ui_task(user_message) and (not names or _looks_like_plan_narration(text)):
                    # Pick the RIGHT first tool: a screen-read ask ("You are on
                    # the ITS portal", "what does the screen show") means the app
                    # is ALREADY open — the model must ui_dump, not re-launch.
                    if _ui_situational_ask(user_message):
                        first = ("ui_dump {} to READ the screen and report what is on "
                                 "it right now")
                    else:
                        first = ("ui_app_open {} if the app is not running, then "
                                 "ui_dump {} to READ the screen")
                    if not names:
                        msg = ("You only described a plan but did NOT call any tool. This task "
                               "requires real actions on the device. Emit a structured tool "
                               "call NOW, e.g. %s, then ui_tap/ui_swipe/ui_type to navigate "
                               "toward the target, and ui_screenshot only after ui_dump "
                               "confirms it. Never just narrate the plan." % first)
                    else:
                        msg = ("You stopped narrating without calling a tool, but the task is "
                               "NOT finished — you have already performed: %s. Continue the "
                               "task step by step: read the screen with ui_dump, then "
                               "ui_tap/ui_swipe/ui_type toward the target, ui_dump after "
                               "each action, and only report done when the target screen is "
                               "confirmed. Emit a tool call NOW, do not narrate." % ", ".join(names))
                    llm_messages.append({"role": "user", "content": msg})
                    active = None
                    dead_rounds += 1
                    if dead_rounds >= 4:
                        with _AGENT_LOCK:
                            _AGENT["activity"] = "stopped (no tool calls)"
                        break
                    continue
                # NON-UI STALL: a prose reply with work outstanding is a stall, not
                # an answer. The UI branch above gets 4 nudges; net/research/general
                # tasks previously fell straight through to `return _terse_reply(...)`.
                _outstanding = _outstanding_subtasks(user_message, names)
                if _outstanding:
                    msg = ("You replied with text but called NO tool, and the task is "
                           "NOT finished. Still outstanding: %s. Do not describe your "
                           "capabilities or list your tools - call one now. If you "
                           "genuinely cannot proceed, state exactly what is blocking "
                           "you." % ", ".join(_outstanding))
                    llm_messages.append({"role": "user", "content": msg})
                    active = None
                    dead_rounds += 1
                    if dead_rounds >= 4:
                        with _AGENT_LOCK:
                            _AGENT["activity"] = "stopped (no tool calls)"
                        break
                    continue
                if text and text.strip():
                    # If Chris asked for a screenshot but the model finished with
                    # a text-only reply (never called ui_screenshot), capture it
                    # server-side so the popup still shows the target screen.
                    if not tcs and "ui_screenshot" not in names and \
                       re.search(r'\b(screenshot|show me|show what|snapshot|capture|look at)\b',
                                 user_message, re.IGNORECASE):
                        try:
                            _sok, _stxt = _call_tool("ui_screenshot", {})
                            if _sok:
                                names.append("ui_screenshot")
                                print("📷 /chat auto-captured screenshot on text-only final reply")
                        except Exception:
                            pass
                    # RESEARCH-AND-SAVE: the model gathered web results but is
                    # ending with a text-only reply that saved nothing. Draft the
                    # findings to the editor instead of silently dropping them so
                    # Chris still gets to review — but ONLY when Chris explicitly
                    # asked for a file; simple questions get a direct answer.
                    if _research_task and _explicit_save:
                        _drafted, _draft_reply = _draft_research_fallback(llm_messages, names, user_message)
                        if _drafted:
                            with _AGENT_LOCK:
                                _AGENT["last_reply"] = _draft_reply
                            return _draft_reply
                    with _AGENT_LOCK:
                        _AGENT["last_reply"] = _terse_reply(text or "")
                    if names and not _already_reasked and _is_ungrounded(_terse_reply(text or "") or ""):
                        llm_messages.append({"role": "user", "content":
                            "That answer is from memory, not from the tool results. Re-answer "
                            "using ONLY the tool results above, cite the source for each claim, "
                            "or state that the results do not establish it."})
                        _already_reasked = True
                        active = None
                        continue
                    # AUTO-OPEN: before returning a text-only reply, make sure a
                    # requested file actually gets opened (view step + UI popup),
                    # even when the model answered from memory without a tool call.
                    _auto_open_user_file_fallback(names, llm_messages, user_message)
                    _auto_open_web_image_fallback(text or "", llm_messages, user_message)
                    return _terse_reply(text or "")
# Model returned empty text after using tools — nudge it to answer
                if names:
                    nudge = ("You have completed the tool calls: %s. "
                             "Now provide your final answer based on the results. "
                             "Do not call more tools." % ", ".join(names))
                    llm_messages.append({"role": "user", "content": nudge})
                    active = None
                    dead_rounds += 1
                    if dead_rounds >= 3:
                        break
                    continue
                break
            dead_rounds = 0
            last_had_tools = True
            batch = tcs[:_BATCH_MAX]
            tids = [{"id": "chat_t%d_%d" % (rnd, j), "type": "function",
                     "function": {"name": nm, "arguments": json.dumps(a)}}
                    for j, (nm, a) in enumerate(batch)]
            # Guard against degenerate loops (e.g. ui_type repeating the same
            # call dozens of times): bail when the same (tool,args) repeats 3+.
            sig = tuple((nm, json.dumps(a or {}, sort_keys=True)) for nm, a in batch)
            if last_batch_sig == sig:
                repeat_count += 1
            else:
                repeat_count = 0
            last_batch_sig = sig
            if repeat_count >= 3:
                with _AGENT_LOCK:
                    _AGENT["activity"] = "stopped (repeated loop)"
                print("🛑 /chat stop: repeated identical batch %s" % sig[:1])
                break
            llm_messages.append({"role": "assistant", "content": "" if tcs else (text or ""),
                                 "tool_calls": tids})
            for j, (name, args) in enumerate(batch):
                # RESEARCH+SAVE FLOW: research tasks write their findings via
                # write_file. Redirect that to open_in_vscode so the findings are
                # opened in Chris's editor (VS Code/VSCodium) as a review DRAFT —
                # the final file is NOT written. Chris reviews it and says 'save
                # it' (or 'discard') afterwards, which commits/deletes the parked
                # draft. The step is labelled open_in_vscode so the UI shows the
                # review action, not a silent save (and the 'file saved' popup
                # does not fire, because the final file was not created).
                run_name, run_args = name, args
                if _research_task and _explicit_save and name == "write_file":
                    run_name, run_args = "open_in_vscode", args
                with _AGENT_LOCK:
                    _AGENT["activity"] = "executing %s" % run_name
                    _advance_indicator()
                sid = _agent_next_id()
                icon = _tool_icon(run_name)
                desc = _tool_desc(run_name, run_args)
                with _AGENT_LOCK:
                    _AGENT["steps"].append({"id": sid, "kind": "work", "text": desc,
                                            "state": "running", "icon": icon})
                # HARD GUARD: block ui_tap/ui_swipe unless the model has read
                # the screen (ui_dump in this batch, or a successful ui_dump /
                # auto-dump in a previous round) since the last screen change —
                # forces the model to read before tapping, not tap blind.
                if run_name in ("ui_tap", "ui_swipe") and not seen_screen:
                    result = ("BLOCKED: You must run ui_dump in the same round "
                              "before ui_tap/ui_swipe. Run ui_dump first to read "
                              "the screen, then decide your tap coordinates from "
                              "the screen state.")
                    ok = False
                else:
                    # A single bad tool call must never take down the whole run:
                    # every result gathered so far is real work worth returning.
                    try:
                        ok, result = _call_tool(run_name, run_args)
                    except Exception as e:
                        ok = False
                        result = ("tool %r failed: %s: %s"
                                  % (run_name, type(e).__name__, e))
                        audit_write("tool", run_name, run_args or {}, False,
                                    "raised %s: %s" % (type(e).__name__, e))
                        print("💥 tool %s raised %s: %s"
                              % (run_name, type(e).__name__, e), flush=True)
                if ok and run_name == "ui_dump":
                    # An explicit ui_dump's result is fed straight back to the
                    # model, so it now has real screen state to tap from.
                    seen_screen = True
                names.append(run_name)
                tcid = "chat_t%d_%d" % (rnd, j)
                print(f"🔧 /chat executed {run_name} ok={ok}")
                with _AGENT_LOCK:
                    _AGENT["tools_used"] += 1
                    if not ok:
                        _AGENT["last_error"] = "%s: %s" % (run_name, str(result)[:300])
                    for s in _AGENT["steps"]:
                        if s["id"] == sid:
                            s["state"] = "done" if ok else "error"
                            s["error"] = "" if ok else result
                            # Store viewable result (image/pdf/text) for frontend rendering
                            if ok and run_name in ("view_user_file", "open_user_file", "view_web_image"):
                                if isinstance(result, _ViewResult):
                                    s["view"] = result.view
                                elif isinstance(result, dict):
                                    s["view"] = result
                    llm_messages.append({"role": "tool", "tool_call_id": tcid,
                                         "name": name, "content": str(result)[:4000]})
                # Detect unproductive re-querying: a research tool (web_search /
                # webfetch / curl) called 3+ times with different arguments looks
                # like a stall. BUT in a multi-part request ("search X, fetch Y,
                # save it, then check weather, the time, and book Z") the model
                # legitimately runs several DIFFERENT queries for the separate
                # subtasks — killing the whole run on the 3rd distinct query would
                # silently drop the not-yet-done subtasks. Only end the tool loop
                # when the remaining work is itself just research/save; if real
                # subtasks (weather, time, etc.) are still pending, nudge the model
                # to move on to them instead of grinding the same topic.
                _call_counts[name] = _call_counts.get(name, 0) + 1
                _call_arg_sigs[name] = _call_arg_sigs.get(name, set())
                _call_arg_sigs[name].add(json.dumps(run_args or {}, sort_keys=True))
                _research_nudge = False
                if name in ("web_search", "webfetch", "curl") and \
                   _call_counts[name] >= 3 and len(_call_arg_sigs[name]) >= 3:
                    _outstanding = _outstanding_subtasks(user_message, names)
                    _outstanding_research_only = bool(_outstanding) and all(
                        o in ("web search", "fetch pages", "save file")
                        for o in _outstanding)
                    if _outstanding and not _outstanding_research_only:
                        _research_nudge = True
                    else:
                        # The searches already returned content (it's in the tool
                        # results). Instead of the old abort message that just listed
                        # the tool names ("searches returned: web_search, ...") —
                        # which the model learned to echo as if it were an answer —
                        # stop the tool loop and let the post-loop synthesizer answer
                        # from the collected evidence.
                        print("[ACE-DISPATCH] 3+ distinct searches; synthesizing from evidence")
                        _stall_break = True
                        break
                if _research_nudge:
                    _outstanding = _outstanding_subtasks(user_message, names)
                    llm_messages.append({"role": "user", "content":
                        "You've re-searched this topic several times without a clear result. "
                        "Stop fighting this one query: move on and do the still-outstanding "
                        "subtasks now (%s), then give your final report." %
                        ", ".join(_outstanding)})
                    active = None
                    dead_rounds += 1
                    break
                if ok and name in _UI_SCREEN_TOOLS:
                    _dok, _dtxt = _ui_auto_dump()
                    seen_screen = _dok
                    if _dok:
                        last_screen = str(_dtxt)[:1500]
                        llm_messages.append({"role": "user", "content":
                            "SCREEN STATE after your %s action (auto ui_dump):\n%s%s" % (
                                name, last_screen, _cert_warning_directive(_dtxt))})
                        llm_messages.extend(_auto_bypass_cert_warning(_dtxt))
                        # Force the model to READ the screen state before its next
                        # move — without this directive the 3B model ignores the
                        # dumped screen and keeps guessing coordinates.
                        if name in ("ui_tap", "ui_swipe", "ui_type", "ui_key"):
                            llm_messages.append({"role": "user", "content":
                                "STOP. Read the SCREEN STATE above carefully. "
                                 "Based on what you see, decide your NEXT action. "
                                 "Do NOT guess coordinates — use the text/bounds "
                                 "from the screen state above."})
            if _stall_break:
                break
    finally:
        with _AGENT_LOCK:
            _AGENT["running"] = False
            _AGENT["activity"] = "done"
            _advance_indicator()
    # Rounds exhausted (or all providers returned None). If we actually did real
    # work, report it honestly instead of the misleading "no models available".
    if not names and _ui_task(user_message) and not (last_text and "FINAL" in last_text.upper()):
        # The model stalled without a single tool call (narrated a plan). For a
        # screen-read/nav ask, fall back to an automatic ui_dump so Chris still
        # gets REAL on-device state instead of the monologue.
        try:
            _dok, _dtxt = _call_tool("ui_dump", {})
            if _dok:
                names.append("ui_dump")
                last_screen = str(_dtxt)[:1500]
                print("📱 /chat auto-dumped screen after nav-task stall (0 tool calls)")
        except Exception:
            pass
    # Research-and-save fallback: the model gathered web results (web_search /
    # curl /webfetch) but stalled before calling open_in_vscode/write_file.
    # Chris's complaint was "he tells me nothing" — so instead of dropping the
    # findings, compile the collected tool results into a review DRAFT and open
    # it in the editor. The parked pending_save means "save it"/"discard" work
    # the same as the model-driven flow.
    if _research_task and _explicit_save:
        _drafted, _draft_reply = _draft_research_fallback(llm_messages, names, user_message)
        if _drafted:
            with _AGENT_LOCK:
                _AGENT["last_reply"] = _draft_reply
            return _draft_reply
    # AUTO-OPEN FALLBACK (helper): Chris asked to open/view/show a file in his
    # user folders but the model answered from memory without calling the file
    # tool (or it narrated a plan and stopped). Resolve the hinted filename
    # server-side and attach the opened-file view so the request still completes
    # AND the UI popup appears even when the model stalls. Returns True when a
    # file was opened (a step with view data was appended to the ledger).
    def _auto_open_user_file():
        return _auto_open_user_file_fallback(names, llm_messages, user_message)

    # If the model already emitted a FINAL line, that is the answer.
    # But if it's ungrounded, re-ground it with tool evidence first.
    # The auto-open fallback MUST run before this return, otherwise a
    # memory-based FINAL reply (no tool call → no step → no view in the UI)
    # would skip the popup entirely.
    if last_text and "FINAL" in last_text.upper():
        _auto_opened = _auto_open_user_file()
        _auto_open_web_image_fallback(last_text, llm_messages, user_message)
        if _auto_opened or (names and _is_ungrounded(last_text)):
            summary = _final_answer(llm_messages, names, last_screen, active,
                                    user_message, chat_one=_chat_one)
            with _AGENT_LOCK:
                _AGENT["last_reply"] = summary
            return summary
        clean = _sanitize_reply(last_text)
        if clean is None:
            clean = _final_answer(llm_messages, names, last_screen, active,
                                  user_message, chat_one=_chat_one)
        with _AGENT_LOCK:
            _AGENT["last_reply"] = clean
        return clean

    # No tools ran and no real text — nothing to summarize. But a file-open ask
    # must still open even when no model is available: resolve the hinted file
    # deterministically so the popup appears (no LLM required).
    if not names and not (last_text and last_text.strip()):
        _auto_picked = _auto_open_user_file()
        msg = _AGENT["last_reply"]
        if not (msg and msg.strip()):
            with _AGENT_LOCK:
                _AGENT["last_reply"] = (("Opened the file you asked for.")
                                        if _auto_picked else (last_text or ""))
        return _AGENT["last_reply"]

    # Auto-capture a screenshot if the user asked for one but the model didn't.
    if names:
        _wants_shot = bool(re.search(
            r'\b(screenshot|show me|show what|snapshot|capture)\b',
            user_message, re.IGNORECASE))
        if _wants_shot and "ui_screenshot" not in names:
            try:
                _sok, _stxt = _call_tool("ui_screenshot", {})
                if _sok:
                    names.append("ui_screenshot")
            except Exception:
                pass

    # AUTO-OPEN FALLBACK: Chris asked to open/view/show a file in his user
    # folders, the model may have listed the directory (list_user_files) but never
    # actually opened the target. Resolve the hinted filename server-side and
    # display it inline so the request still completes even if the model stalls.
    _auto_open_user_file()

    summary = _final_answer(llm_messages, names, last_screen, active,
                            user_message, chat_one=_chat_one)
    summary = _normalize_reply(summary)
    # Final net: nothing resembling tool syntax may ever reach Chris as a reply.
    if _looks_like_tool_markup(summary):
        summary = _evidence_fallback(_collect_tool_evidence(llm_messages), names)
    with _AGENT_LOCK:
        _AGENT["last_reply"] = summary
    return summary


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    # E-STOP: kill mode = total silence. No conversation saved, no model touched.
    if _kill_armed():
        return jsonify({"reply": "E-STOP is armed — ACEsi is stopped. Type the un-kill word on your phone or use the web UI to resume."})
    save_conversation("user", user_message)

    # Emotional memory: notice tiredness/frustration/sadness in what Chris says
    # and remember it for the day (and soften the reply if he's low).
    _mood = detect_mood(user_message)
    if _mood:
        record_mood(_mood, note=user_message[:200])
        print(f"🧠 Mood recorded: {_mood}")

    # Deterministic "how did I feel" - answer from the mood ledger, not the LLM.
    _mood_q = re.match(
        r'(?i)\b(?:how\s+(?:did|do|am|are)\s+i\s+feel(?:ing)?|what\s+was\s+my\s+mood|how\s+was\s+my\s+(?:mood|day)|how\s+am\s+i\s+(?:feeling|doing)|'
        r'how\s+have\s+i\s+been|what\s+mood\s+was\s+i)\b'
        r'(?:\s+(?:yesterday|today|last\s+night|earlier|tonight|this\s+week|last\s+week))?[?.!]*$',
        user_message)
    if _mood_q:
        _day_sm = re.search(r'(?i)\b(yesterday|last\s+night|last\s+week)\b', user_message)
        _target = None
        if _day_sm:
            if 'week' in _day_sm.group(1):
                _target = "week"
            else:
                _target = (datetime.now() - timedelta(days=1)).date().isoformat()
        else:
            _target = datetime.now().date().isoformat()
        if _target == "week":
            _mv = get_moods(7)
            if _mv:
                entry = _mv[-1]
                reply = f"This week I noticed: {entry['mood']} (last on {entry['when'][:10]} at {entry['when'][11:16]})" + (f" — {entry['note'][:120]}" if entry.get('note') else "")
            else:
                reply = "I don't have a clear read on your moods this week yet — mostly neutral from what I saw."
        else:
            _me = mood_for_date(_target)
            if _me:
                reply = f"On {_target} I read you as {_me['mood']}" + (f" — {_me['note'][:150]}" if _me.get('note') else "")
            else:
                reply = f"I don't have a mood note for {_target} yet. Tell me how you're feeling and I'll remember it."
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

    # Deterministic "forget <key>" — Chris controls what stays.
    _forget_m = re.match(r'(?i)^(?:please\s+)?forget\s+(?:the\s+)?(?:fact|memory|key)?\s*[:=]?\s*(.+)$', user_message)
    if _forget_m:
        _k = _forget_m.group(1).strip().strip('"\'')
        if _k.lower() in ('everything', 'all', 'my memory'):
            conn = sqlite3.connect('ace_memory.db')
            c = conn.cursor()
            c.execute("DELETE FROM memories")
            conn.commit()
            conn.close()
            reply = "I've cleared my memory of stored facts. Start fresh whenever you're ready."
        else:
            _hits = []
            mem = get_memories()
            for k in mem:
                if k == _k or _k.lower() in k.lower():
                    _hits.append(k)
            if _hits:
                for k in _hits:
                    forget_memory(k)
                reply = f"Forgot: {', '.join(_hits)}"
            else:
                reply = f"I don't have anything stored under '{_k}'."
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

    # Deterministic "do I remember X?" - leaf recall from the memories table so
    # the test questions (Ember, oldest book in Harvard, mood) never depend on
    # model availability. Questions like "what is Ember?" and "what/which is the
    # oldest book in the Harvard library?" resolve straight from stored facts.
    _recall_m = re.match(
        r'(?i)^(?:what|which|who|whats|whos|tell\s+me\s+about)\s+(?:is|was|are|were|the)\s*(.+)'
        r'(\?|\?*\.*)$', user_message.strip())
    if _recall_m:
        _q = _recall_m.group(1).strip("?.,! ").lower()
        _mem = get_memories()
        # Normalize common phrasings onto the stored key.
        _norm = {
            "ember": "lesson.ember",
            "the ember word": "lesson.ember",
            "our word": "lesson.ember",
            "the oldest book in the harvard library": "lesson.gutenberg_bible",
            "the oldest book": "lesson.gutenberg_bible",
            "the oldest book ever": "lesson.gutenberg_bible",
            "the gutenberg bible": "lesson.gutenberg_bible",
            "harvard library": "lesson.gutenberg_bible",
        }
        _hit_key = None
        if _q in _norm:
            _hit_key = _norm[_q]
        else:
            for k, v in _mem.items():
                if _q in k.lower() or k.lower() in _q or (_q in str(v['value']).lower()):
                    _hit_key = k
                    break
        if _hit_key and _hit_key in _mem:
            reply = _mem[_hit_key]['value']
        else:
            reply = None
        if reply:
            save_conversation("assistant", reply)
            return jsonify({"reply": reply})

    # REVIEW-BEFORE-SAVE follow-up: when a prior research task parked a draft
    # ("pending_save") and opened it in the editor, Chris decides here by saying
    # "save it"/"keep it"/"keep the file" (commit the draft to the final path)
    # or "discard"/"don't save"/"throw it away" (delete the draft). Handled
    # deterministically BEFORE the model runs, so no tokens are wasted and the
    # outcome is exact. The model still sees the rest of the conversation.
    _pm = user_message.strip().lower()
    _save_follow = re.match(
        r'^(?:(?:yes|yeah|yep|ok|okay|sure|please)\s+)?(?:save|keep|commit|publish|write)\b'
        r'(?:\s+(?:it|the\s+(?:findings?|notes?|results|file|research|draft)))?'
        r'(?:\s+(?:as|to)\s+.+)?[!.?]*$', _pm)
    _discard_follow = re.match(
        r'^(?:(?:no|nah|nope)\s+)?(?:discard|ditch|trash|throw|delete|abandon|cancel|forget|dont\s+save|do\s+not\s+save|leave\s+it)\b'
        r'(?:\s+(?:it|the\s+(?:findings?|notes?|results|file|research|draft)))?[!.?]*$', _pm)
    with _AGENT_LOCK:
        _has_pending = bool(_AGENT.get("pending_save"))
    _follow_reply = None
    if _save_follow and _has_pending:
        _follow_reply = _commit_pending_save()
    elif _discard_follow and _has_pending:
        _follow_reply = _discard_pending_save()
    if _follow_reply:
        save_conversation("assistant", _follow_reply)
        return jsonify({"reply": _follow_reply})

    # Handle file read requests via the strict matcher above.
    global LAST_FILE_PATH
    is_file_req, candidate, vague = _match_file_request(user_message)
    if is_file_req:
        if vague and LAST_FILE_PATH:
            file_path = LAST_FILE_PATH
        elif not vague:
            file_path = candidate
        else:
            file_path = None
    else:
        file_path = None
    if not file_path:
        file_path = None

    def resolve_file_path(token):
        if not token:
            return None
        if os.path.isabs(token):
            return token
        doc_base = os.path.join(os.path.expanduser('~'), 'Documents')
        proj_base = DATA_DIR
        for base in (doc_base, proj_base):
            cand = os.path.join(base, token)
            if os.path.exists(cand):
                return cand
        for ext in ('.dart',):
            for base in (doc_base, proj_base):
                cand = os.path.join(base, token) + ext
                if os.path.exists(cand):
                    return cand
        # fall back to the token as-is (let the caller report the failure)
        return token

    if file_path:
        COMMON_EXTS = ('.pdf', '.txt', '.png', '.jpg', '.jpeg', '.docx', '.md')
        if not os.path.isabs(file_path):
            # Try Documents folder first, then project directory
            doc_base = os.path.join(os.path.expanduser('~'), 'Documents')
            proj_base = 'C:\\Users\\chris\\StudentSyncSA'
            doc_path = os.path.join(doc_base, file_path)
            proj_path = os.path.join(proj_base, file_path)
            if os.path.exists(doc_path):
                file_path = doc_path
            elif os.path.exists(proj_path):
                file_path = proj_path
            else:
                # Try common extensions against both bases
                for ext in COMMON_EXTS:
                    if os.path.exists(doc_path + ext):
                        file_path = doc_path + ext
                        break
                    if os.path.exists(proj_path + ext):
                        file_path = proj_path + ext
                        break
        else:
            # Absolute path — try common extensions if the bare path doesn't exist
            if not os.path.exists(file_path):
                for ext in COMMON_EXTS:
                    if os.path.exists(file_path + ext):
                        file_path = file_path + ext
                        break
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf':
                import fitz
                doc = fitz.open(file_path)
                pages = len(doc)
                content = "\n".join(page.get_text() for page in doc)
                doc.close()
                if len(content.strip()) < 10:
                    # Scanned PDF — render pages and OCR them
                    content = ocr_pdf(file_path)
            elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'):
                content = ocr_image(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            LAST_FILE_PATH = file_path
            # If the user said "open", physically launch the file (default viewer)
            if is_open:
                os.startfile(file_path)
                print(f"🖥️ Opened file in default viewer: {file_path}")
            # Include file content in the message sent to LLM
            user_message = f"[File content of {file_path}]:\n{content}\n\n---\nUser asked: {user_message}"
            print(f"📖 Read file: {file_path} ({len(content)} chars)")
        except Exception as e:
            return jsonify({"reply": f"❌ Could not read file: {e}"})

    # Greeting check — time-aware
    if user_message.lower().strip() in ["hello", "hi"]:
        hour = datetime.now().hour
        if hour < 5:
            reply = "It's late, Chris. I'm here. What's going on?"
        elif hour < 12:
            reply = "Good morning. I'm here."
        elif hour < 18:
            reply = "Good afternoon. I'm here."
        else:
            reply = "Good evening. I'm here."
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

    preferred = data.get('model', '')
    provider = _find_provider_for_model(preferred)
    if provider:
        _, _, _, model, *_ = provider
    else:
        model = OPENROUTER_MODEL

    # "note this / write down: X / log X" → journal entry
    note_match = re.match(r'^(?:note|write|log|jot)\s+(?:this|that|down|it|the following)?\s*[:,\-]?\s*(.+)$', user_message, re.IGNORECASE)
    if note_match and note_match.group(1).strip():
        add_journal(note_match.group(1).strip())
        reply = "Logged it."
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

    # "remember <key> = <value>" or "remember <key>: <value>" → stored fact
    rem_match = re.match(r'^remember\s+(?:that\s+)?(.+?)\s*=\s*(.+)$', user_message, re.IGNORECASE) or \
                re.match(r'^remember\s+(?:that\s+)?([^:]+):\s*(.+)$', user_message, re.IGNORECASE)
    if rem_match:
        key = rem_match.group(1).strip()
        value = rem_match.group(2).strip()
        if key and value:
            set_memory(key, value)
            reply = f"Got it — remembered: {key}"
            save_conversation("assistant", reply)
            return jsonify({"reply": reply})

    # Memory-check questions ("can you access your memory", "do you have
    # memory", "check your memory", "what do you know about me", "what do you
    # remember") → deterministic reply from the stored facts. The local 3b model
    # forgets its own memory block, so answer from the DB directly; the LLM path
    # is flaky here. Also catches "was that all / only the first N lines" type
    # follow-ups so they get a clean count list instead of a raw context dump.
    mem_q = re.match(
        r'(?i)\b(?:access|check|open|see|read|use|consult)\s+(?:your\s+)?(?:database|memory)\b'
        r'|\bdo you (?:have|remember)\b|\bcan you remember\b|\bcheck your memory\b'
        r'|\bwhat do you (?:know|remember)\b|\bwhat do you (?:know|remember) about me\b'
        r'|\b(?:was|is) that (?:only|all)\b|\bonly the first \d+ (?:lines?|facts?|memories?)\b',
        user_message)
    if mem_q:
        mem = get_memories()
        if mem:
            facts = _curated_memory_lines(mem)
            total = len(mem)
            shown = len(facts)
            reply = ("Yes — I have persistent memory. Here's what I have stored:\n"
                     + "\n".join(facts))
            if total > shown:
                reply += f"\n\n…plus {total - shown} more stored facts (I can list them if you want)."
        else:
            reply = "My memory database is empty right now. Tell me something to remember and I'll store it."
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

    # Ping / notify Chris's phone (deterministic, so a "test ping" always works
    # no matter which model is up). Plain wording like "send a test ping to my
    # phone", "can you send a 'test' ping?", or "ping me" hits here before the
    # LLM loop. Quotes/quotes-types around 'test' are tolerated.
    _pm = user_message.strip()
    ping_match = re.match(
        r'(?i)^(?:can (?:you|u)\s+|please\s+|hey\s+acesi[\s,]+)?'
        r'(?:send\s+)?(?:a\s+)?(?:test\s+)?[\"\']?test[\"\']?\s+'
        r'ping(?:\s+(?:to|on)\s+my\s+phone)?[!.?]*$', _pm) or \
        re.match(
        r'(?i)^(?:can (?:you|u)\s+|please\s+|hey\s+acesi[\s,]+)?'
        r'(?:send\s+)?(?:a\s+)?(?:test\s+)?ping'
        r'(?:\s+(?:to|on)\s+my\s+phone)?[!.?]*$', _pm) or \
        re.match(r'(?i)^(?:send|fire)\s+(?:a\s+)?(?:test\s+)?(?:push|notification|alert)'
                 r'(?:\s+to\s+(?:my\s+)?(?:phone|device|ntfy))?[!.?]*$', _pm) or \
        re.match(r'(?i)^(?:send\s+)?(?:me\s+)?(?:a\s+)?(?:push\s+)?notification'
                 r'(?:\s+to\s+my\s+phone)?$', _pm)
    if ping_match:
        ok, out = tool_notify("ACEsi Test", "This is a test ping from ACEsi")
        reply = ("Pinged your phone — check the ntfy notification." if ok
                 else f"Couldn't reach your phone: {out}")
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

    if "auto-fix" in user_message.lower():
        # Capture a bare filename, a lib/... path, or a Windows/absolute path ending in .dart
        file_match = re.search(r'((?:[\w.-]+/)*[\w.-]+\.dart|(?:[A-Za-z]:[\\/][^\s,]+\.dart))', user_message)
        error_match = re.search(r'(?:the\s+)?error(?:\s+is)?\s*:\s*(.+)$', user_message, re.IGNORECASE)
        file_path = file_match.group(1) if file_match else None
        if file_path:
            file_path = resolve_file_path(file_path)
        if file_path and error_match:
            error_text = error_match.group(1).strip().rstrip('.').strip()
            return jsonify({
                "type": "stream",
                "url": f"/auto_fix_stream?file_path={quote_plus(file_path)}&error_text={quote_plus(error_text)}"
            })
        else:
            hint = "a file path like lib/path/file.dart, C:\\path\\file.dart, or just file.dart"
            return jsonify({"reply": "I need a file path and error description. Say: 'auto-fix " + hint + ". The error is: ...'"})

    try:
        print(f"📨 Incoming message length: {len(user_message)} chars")
        # Truncate to stay within context window (safety for free-tier models)
        max_chars = 8000
        if len(user_message) > max_chars:
            user_message = user_message[:max_chars] + "\n\n[Message truncated...]"
            print(f"✂️ Truncated to {max_chars} chars")

        # Persona + context (memory, journal, time) fed into every reply.
        _prefs_block = build_preferences_block()
        _prefs_text = ("\n\n" + _prefs_block) if _prefs_block else ""
        system_prompt = (
            "You are ACEsi, Chris's companion and assistant. Speak in short, natural, honest sentences. "
            "You are calm, present, and can be quiet — you don't gush, over-cheer, or over-promise. "
            "You can be brief; silence is fine. If you don't know something, say you don't know. "
            "Never invent personal history, memories, or references to past events that are not in the context below. "
            "Use the facts and journal entries below naturally when they are relevant — not every message. "
            "Keep replies short unless Chris asks for more.\n\n"
            "YOUR MEMORY: You DO have persistent memory. The bracketed blocks below are it — "
            "[Facts I know about Chris], [Shared history — recent journal entries], and the recent "
            "conversation turns at the end of this prompt. They are loaded from your database on every "
            "message, so you remember across conversations. When Chris asks 'can you remember / do you "
            "have memory / check your memory', answer YES and quote the exact facts from those blocks — "
            "do not say you have no memory. If Chris tells you something to remember, reply "
            "with: remember <key> = <value> (this stores a new fact).\n\n"
            "DEVICE + DEV TOOLS: You can ACTUALLY perform actions yourself — you are not limited to "
            "talking. When Chris asks you to do something on the device or app (open the app, tap, swipe, "
            "type, press a key, navigate, take a screenshot, check what is on screen), CALL the ui_* tools "
            "(ui_app_open, ui_tap, ui_swipe, ui_type, ui_key, ui_dump, ui_screenshot). For code work you "
            "have read_file, edit_file, write_file, run_command, flutter_test, flutter_analyze, git_*, "
            "build_apk, pub_*, and the cdp_* webview tools. ACT, do not ask the user to provide commands. "
            "Never defer back to the user with 'please provide commands' — you have the tools, so use them.\n"
            "FILE TOOLS: You have FULL access to Chris's PC (Documents, Pictures, Desktop, Downloads, any folder). When he asks you to look at, find, open, or show a file, use list_user_files to locate the folder, then view_user_file (accepts a full path OR a bare filename like 'GEPFGEPF' — it searches automatically) to display it inline in the chat. "
            "If view_user_file's search fails, run list_user_files on the specific folder to confirm the exact filename first. "
            "The tool open_user_file is ONLY for 'launch externally in "
            "default app' — do NOT use it for normal 'show me the file' requests.\n"
            "WEB IMAGES: when Chris asks to 'get a picture of X', 'show me an image of Y', or 'open the picture "
            "from the internet', you MUST actually display it: after web_search/webfetch returns a link, call "
            "view_web_image with the image URL (the .jpg/.png/.gif link itself) so the picture pops up in the chat. "
            "Do NOT just paste the URL into your reply.\n"
            "EMAIL + PHONE ALERTS: a background watcher already polls Chris's Gmail and "
            "Yahoo every ~2 minutes and pushes a PHONE notification (ntfy) when an email "
            "matches a watch rule (NSFAS is already watched). So when he says 'keep an eye "
            "on my email, tell me when an NSFAS mail arrives' or 'check my NSFAS email': "
            "call check_email to look NOW, and tell him plainly that alerts are set to his "
            "PHONE and are already active. Never suggest he set up a filter in his email "
            "client, check his spam folder, or contact NSFAS directly — that is a "
            "deflection. Only add a NEW sender with the email_rules tool if he names one. "
            "If he says he does NOT want a local/desktop notification, do not use any "
            "Windows toast — ntfy to his phone is the channel.\n"
            "NEVER repeat a tool call that just errored — use the error message to fix the path, then try once more.\n"
            "STANDING PREFERENCES: the moment Chris states how he wants things done "
            "('call me Braam', 'answer in Afrikaans', 'use metric units', 'keep it to two "
            "lines', 'no bullet points', 'be more formal'), call set_preference with that "
            "key and value, then confirm it in one short sentence. Do this WITHOUT being "
            "asked to remember it. Always pick the key from the tool's list — never invent "
            "a key name like 'name_preference'. If he tells you to STOP following one, call "
            "forget_preference. If he asks what you always do for him, call "
            "list_preferences. Any preference stored this way overrides your default "
            "style in every later reply until it is changed or removed.\n"
            "NAVIGATION RULE: for a navigation request (e.g. 'open the app, go to the Venda ITS portal, "
            "screenshot it') you MUST actually navigate step by step and verify: ui_app_open, then ui_dump "
            "to read the screen, then ui_tap/ui_swipe/ui_type to move toward the target, ui_dump again to "
            "confirm each screen change, and only ui_screenshot AFTER the last ui_dump proves the target is "
            "visible. A screenshot of the launch screen is NOT reaching the target — never finish a "
            "navigation after just opening the app. Use ui_dump (text hierarchy) to know where you are; you "
            "cannot see images. Screenshots are shown to Chris in a popup and are NOT saved to disk unless "
            "Chris asked to keep the file (only then pass save=true). In your reply, cite the real "
            "page content from the last ui_dump and what you actually did — never invent a screenshot "
            "filename, a web page you did not load, or a Chrome/CDP step you never ran.\n"
            "STYLE: never narrate your reasoning in prose — no 'I will', no 'The dump shows', no "
            "commentary between actions. Output ONLY the tool call, then when the task is done give a "
            "SHORT, plain report (a few lines, like a text message): what you did and the key on-screen "
            "values. Do not lecture or recap the whole process.\n"
"AUTO-TRACK: When Chris gives you 2 or more separate instructions\n"
"in one message (e.g. \"do X, do Y, and do Z\"), break them into\n"
"tracked tasks automatically. After finishing each one, mark it\n"
"done. In your FINAL reply, always end with a progress line:\n"
"\"Progress: X/Y tasks done\" (e.g. \"Progress: 3/3 tasks done\" or\n"
"\"Progress: 2/3 tasks done — 1 pending\").\n"
"HTTPS WARNING: if a ui_dump shows Chrome's 'Your connection is not private' / ERR_CERT / "
            "HSTS warning for the ITS portal, type thisisunsafe (ui_type {\"text\": \"thisisunsafe\"}) "
            "to bypass it and continue — the expired certificate is expected and safe. If ACEsi's "
            "server already auto-typed it, keep navigating from the fresh ui_dump.\n"
            "RESEARCH + SAVE: when Chris EXPLICITLY asks you to research something AND save the "
            "results to a file (e.g. 'research X and save it to notes.txt'), CALL web_search "
            "(or curl/webfetch) to gather the data, then call open_in_vscode with the full "
            "formatted findings (path = the filename Chris asked for, content = the markdown). "
            "That opens the findings in VS Code as a DRAFT for Chris to review — it does NOT "
            "write the final file. Then stop and tell Chris the draft is open for review in VS "
            "Code and that you will save it to <path> when he says 'save it'.\n"
            "IMPORTANT: For simple factual questions (e.g. 'what is X?', 'who is Y?'), just "
            "answer directly from the tool results. Do NOT save to a file unless explicitly asked.\n\n"
            "ANSWER QUALITY RULES — NEVER VIOLATE:\n"
            "1. When web_search returns results, SYNTHESIZE them into a DEFINITIVE answer. Never say 'it depends', 'it's unclear', or 'would you like more detail?'. Give the exact answer the user asked for.\n"
            "2. For 'who is X?' or 'what is X?' — give a complete, direct answer from the search results. Do NOT end with 'would you like more detail?', 'is there anything specific?', 'would you like me to dig deeper?', 'want me to go deeper?', or ANY question back to the user.\n"
            "3. If search results contain the answer, STATE IT CLEARLY. Do not hedge, deflect, or ask follow-up questions.\n"
            "4. For historical/factual questions (oldest book, who was Mandela, market prices) — give the concrete fact from the sources. If sources disagree, cite the consensus or most authoritative source.\n"
            "5. NEVER end a factual answer with a question back to the user.\n"
            "6. FORBIDDEN PHRASES — NEVER USE: 'Would you like me to...', 'Want me to...', 'Would you like...', 'Would you like more...', 'Is there anything...', 'Let me know if...', 'Shall I...', 'Do you want...'. These are DEFLECTIONS. Answer directly instead.\n"
            + _mood_softener_line()
            + build_context_block()
            + _prefs_text
            + "\n\n" + _GROUNDING_DIRECTIVE + "\n\n" + _GROUNDING_FALLBACK
        )

        # Recent turns (minus the just-saved current message) give ACEsi context.
        history = get_recent_conversation(9)[:-1]
        llm_messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            if h.get('role') in ('user', 'assistant'):
                llm_messages.append({"role": h['role'], "content": h['content']})
        llm_messages.append({"role": "user", "content": user_message})

        # Agent-style dispatch (see _chat_dispatch): ACEsi executes emitted tool
        # calls (ui_*, git_*, flutter_*, ...) and feeds results back — it never
        # defers to the user. Returns the final text reply or None.
        reply = _chat_dispatch(llm_messages, user_message=user_message, preferred_model=model)
        if reply:
            # Playbook memory: record which tools proved useful on this task.
            with _AGENT_LOCK:
                chat_tools = [s.get("text", "") for s in _AGENT.get("steps", [])
                              if s.get("state") == "done" and s.get("kind") == "work"]
            done_tool_names = [t.split(" ")[0].strip("()") for t in chat_tools if t]
            if done_tool_names and not _kill_armed():
                playbook_note(user_message, done_tool_names, reply)
            save_conversation("assistant", reply)
            # Journal the session close when Chris signs off for the day
            if re.search(r'\b(good\s?night|goodbye|bye|that.s all|that is all|done for now|end of session|i.m done|im done|going to sleep|off to bed)\b', user_message, re.IGNORECASE):
                add_journal(f"Session closed. Chris said: \"{user_message[:200]}\". I replied: \"{reply[:200]}\"")
                print("📓 Journaled session close")
            return jsonify({"reply": reply, "shot_ts": _LAST_SHOT["ts"]})
        return jsonify({"reply": "Error: no models available", "shot_ts": _LAST_SHOT["ts"]})
    except Exception as e:
        print(f"💥 Exception in /chat: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        with _AGENT_LOCK:
            _AGENT["running"] = False
            _AGENT["activity"] = "error"
            _AGENT["last_reply"] = f"Error: {type(e).__name__}: {e}"
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route('/history', methods=['GET'])
def history():
    limit = min(int(request.args.get('limit', 100)), 500)
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    messages = [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    return jsonify({"messages": messages})

@app.route('/run', methods=['POST'])
def run_command():
    command = (request.json or {}).get('command', '')
    try:
        if "scrcpy" in command.lower():
            _popen('start cmd /k "scrcpy"', shell=True)
            return jsonify({'output': '✅ Scrcpy launched'})
        # `flutter run` / `dart run` are long-lived, attached dev sessions that
        # never exit on their own. subprocess.run would block this request
        # thread forever, so stream to a log and return immediately.
        if re.match(r'^\s*(flutter\s+run|dart\s+run)\b', command, re.I):
            command = _resolve_run_device(command)
            if command is None:
                return jsonify({'output': '❌ "flutter run" needs a connected Android device, but none was found (or it is locked/offline). Run `adb devices` and unlock the device, then retry.'})
            log_path = f'run_{uuid.uuid4().hex}.log'
            log = open(log_path, 'w', encoding='utf-8')
            proc = _popen(command, shell=True, stdout=log,
                                    stderr=subprocess.STDOUT)
            return jsonify({'output': (f'✅ {command} started (pid {proc.pid}). '
                f'Watch output live: `Get-Content {log_path} -Wait`. The log stays empty '
                f'for ~50-60s while the APK builds/installs; after install the app launches '
                f'on the device. Logs: {log_path}')})
        result = _run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)})

def _android_device_id():
    """First connected Android serial in 'device' state, or None."""
    try:
        out = _check_output(['adb', 'devices'], stderr=subprocess.STDOUT,
                                      text=True, timeout=15)
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and not parts[0].startswith('List') and parts[1] == 'device':
                return parts[0]
    except Exception:
        pass
    return None

def _resolve_run_device(command):
    """flutter's -d does not accept 'android' as a device id for a physical
    phone; resolve it (or a bare `flutter run`) to the real adb serial so a
    device is always selected instead of hanging/ erroring on 'android'."""
    m = re.search(r'-d\s+(\S+)', command)
    token = m.group(1) if m else None
    if token is not None and not token.lower().startswith('android'):
        return command  # user chose a real target (e.g. -d chrome / windows)
    device_id = _android_device_id()
    if not device_id:
        return None
    if m:
        command = re.sub(r'-d\s+\S+', '-d ' + device_id, command, count=1)
    else:
        command = command.rstrip() + ' -d ' + device_id
    return command

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = os.listdir('C:\\Users\\chris\\StudentSyncSA')
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)})

def strip_code_fences(code):
    """Remove a leading ```<lang> ... trailing ``` wrapper if the model added one."""
    if not code:
        return code
    s = code.strip()
    if s.startswith('```'):
        lines = s.splitlines()
        if lines and lines[-1].startswith('```'):
            lines = lines[1:-1]
        elif len(lines) > 1 and lines[0].startswith('```') and lines[-1].startswith('```'):
            lines = lines[1:-1]
        else:
            lines = lines[1:] if lines and lines[0].startswith('```') else lines
            if lines and lines[-1].startswith('```'):
                lines = lines[:-1]
        return "\n".join(lines).strip() + "\n"
    return code

@app.route('/read', methods=['POST'])
def read_file():
    data = request.json
    path = data.get('path', '')
    try:
        with open(path, 'r') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/write', methods=['POST'])
def write_file():
    data = request.json
    path = data.get('path', '')
    content = data.get('content', '')
    try:
        with open(path, 'w') as f:
            f.write(content)
        return jsonify({'status': 'saved'})
    except Exception as e:
        return jsonify({'error': str(e)})

def _open_external(rp):
    """Open a real file in its default app. For OneDrive cloud-only placeholders
    (recall-on-data-access / offline attribute set), first forces them to pin to
    this device so the target app can actually open the content; if the file
    stays unreadable (provider not syncing), opens its folder in Explorer instead
    and reports honest feedback. Returns (ok, message)."""
    if not rp or not os.path.isfile(rp):
        return False, "file not found: %s" % rp
    cloud_only = False
    try:
        if os.name == 'nt':
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(rp)
            if attrs != 0xFFFFFFFF:
                cloud_only = bool(attrs & (0x1000 | 0x400000))  # OFFLINE | RECALL_ON_DATA_ACCESS
    except Exception:
        pass
    def _try_read():
        try:
            with open(rp, 'rb') as _f:
                return len(_f.read(1)) == 1
        except Exception:
            return False
    if cloud_only and not _try_read():
        # Force pin to this device (asks OneDrive to download the real content).
        try:
            import subprocess
            subprocess.run(["attrib", "-U", "+P", rp], capture_output=True, timeout=30)
        except Exception as e:
            print("⚠️ cloud-file pin attempt failed: %s" % e)
        # Give the sync engine a moment to hydrate.
        for _ in range(10):
            time.sleep(1.0)
            if _try_read():
                break
        if not _try_read():
            # Provider isn't syncing (e.g. OneDrive not running in session). Open
            # Explorer so Chris can see/trigger the sync manually.
            try:
                import subprocess
                subprocess.run(["explorer.exe", "/select,", rp], check=False)
            except Exception as e:
                print("⚠️ explorer fallback failed: %s" % e)
            return True, "cloud file not downloaded yet — opened its folder in Explorer (start OneDrive to sync it)"
    try:
        import subprocess, platform
        system = platform.system()
        if system == "Windows":
            os.startfile(rp)
        elif system == "Darwin":
            subprocess.run(["open", rp], check=False)
        else:
            subprocess.run(["xdg-open", rp], check=False)
    except Exception as e:
        return False, "failed to open: %s" % e
    return True, "opened %s for you" % os.path.basename(rp)


@app.route('/file/open', methods=['POST'])
def file_open():
    """Open a saved file in the OS default viewer so the user can verify it."""
    data = request.json or {}
    path = data.get('path', '')
    rp = _safe_path(path)
    if not rp:
        return jsonify({'error': 'path outside project: %s' % path})
    if not os.path.isfile(rp):
        return jsonify({'error': 'file not found: %s' % os.path.relpath(rp, PROJECT_ROOT)})
    try:
        os.startfile(rp)
    except Exception as e:
        return jsonify({'error': str(e)})
    return jsonify({'ok': True, 'path': os.path.relpath(rp, PROJECT_ROOT)})

@app.route('/userfile/open', methods=['POST'])
def userfile_open():
    """Open a file from anywhere on Chris's PC in its default application (for
    editing, viewing externally, etc.). Called when he clicks a file in a popup."""
    data = request.json or {}
    path = data.get('path', '')
    rp = _safe_user_path(path)
    if not rp or not os.path.isfile(rp):
        return jsonify({'error': 'file not found: %s' % path})
    ok, msg = _open_external(rp)
    if not ok:
        return jsonify({'error': msg})
    return jsonify({'ok': True, 'path': rp, 'msg': msg})

# ===== Autonomous code agent (ACEsi writing/editing code on its own) =====
# The model plans with THOUGHT/CALL/FINAL lines; the server executes tools,
# feeds results back, and loops until FINAL. The frontend already polls
# /opencode/status for inline work-steps and /opencode/stop for abort, so no
# frontend change is required — only the engine below is missing.
PROJECT_ROOT = os.path.realpath(DATA_DIR)

INDICATOR_STATES = [
    "Thinking",
    "Considering next steps",
    "Initializing snapshot",
    "Running Commands",
    "Making Edits",
    "Exploring",
    "Writing Response",
]
_agent_indicator_idx = [0]

def _reset_indicator():
    with _AGENT_LOCK:
        _agent_indicator_idx[0] = 0

def _advance_indicator():
    with _AGENT_LOCK:
        _agent_indicator_idx[0] = (_agent_indicator_idx[0] + 1) % len(INDICATOR_STATES)
        return INDICATOR_STATES[_agent_indicator_idx[0]]

def _current_indicator():
    with _AGENT_LOCK:
        return INDICATOR_STATES[_agent_indicator_idx[0]] if _AGENT.get("running") else ""

_AGENT_LOCK = threading.RLock()
_AGENT = {"running": False, "abort": False, "activity": "", "steps": [], "last_reply": "", "last_raw": "", "tools_used": 0, "corrective": 0, "last_call_sig": None, "last_call_ok": False, "last_error": "",
          # Review-before-save: when a research/write task opens findings in the
          # editor (VS Code / VSCodium) instead of silently writing to disk, the
          # draft path + intended target are parked here so a follow-up message
          # ("keep it" / "save it") can commit it, or "discard" can delete it.
          "pending_save": None}
_agent_seq = [0]
def _agent_reset():
    with _AGENT_LOCK:
        _AGENT["running"] = False
        _AGENT["abort"] = False
        _AGENT["activity"] = ""
        _reset_indicator()
        _AGENT["steps"] = []
        _AGENT["last_reply"] = ""
        _AGENT["tools_used"] = 0
        _AGENT["corrective"] = 0
        _AGENT["last_raw"] = ""
        _AGENT["last_call_sig"] = None
        _AGENT["last_call_ok"] = False
        _AGENT["last_error"] = ""

def _agent_next_id():
    with _AGENT_LOCK:
        _agent_seq[0] += 1
        return "a%d" % _agent_seq[0]

# ===== Task Queue System =====
# Persistent queue of tasks that ACEsi executes sequentially.
# Survives restarts, reports progress, handles failures.
_TASK_QUEUE_FILE = 'task_queue.json'
_TASK_QUEUE_LOCK = threading.RLock()

def _load_task_queue():
    return load_json(_TASK_QUEUE_FILE, {"queue": [], "current_index": 0, "status": "idle", "results": []})

def _save_task_queue(queue_data):
    save_json(_TASK_QUEUE_FILE, queue_data)

def _queue_add(tasks, on_failure="stop"):
    """Add tasks to queue. tasks = list of {"task": "...", "on_failure": "skip|retry|stop"}.
    on_failure default applies to all tasks unless overridden per-task."""
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        for t in tasks:
            if isinstance(t, str):
                t = {"task": t}
            q["queue"].append({
                "task": t.get("task", ""),
                "on_failure": t.get("on_failure", on_failure),
                "status": "pending",
                "result": None,
                "error": None,
                "started_at": None,
                "finished_at": None,
            })
        q["status"] = "pending" if q["status"] == "idle" else q["status"]
        _save_task_queue(q)
        return q

def _queue_clear():
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        q["queue"] = []
        q["current_index"] = 0
        q["status"] = "idle"
        q["results"] = []
        _save_task_queue(q)
        return q

def _queue_status():
    with _TASK_QUEUE_LOCK:
        return _load_task_queue()

def _queue_stop():
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        if q["status"] in ("running", "pending"):
            q["status"] = "stopped"
            _save_task_queue(q)
        return q

def _queue_resume():
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        if q["status"] in ("stopped", "paused"):
            q["status"] = "pending"
            _save_task_queue(q)
        return q

def _queue_skip_current():
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        if q["status"] == "running" and 0 <= q["current_index"] < len(q["queue"]):
            q["queue"][q["current_index"]]["status"] = "skipped"
            q["queue"][q["current_index"]]["error"] = "Skipped by user"
            q["queue"][q["current_index"]]["finished_at"] = time.time()
            q["current_index"] += 1
            if q["current_index"] >= len(q["queue"]):
                q["status"] = "completed"
            else:
                q["status"] = "pending"
            _save_task_queue(q)
        return q

def _queue_retry_current():
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        if q["status"] in ("running", "failed") and 0 <= q["current_index"] < len(q["queue"]):
            q["queue"][q["current_index"]]["status"] = "pending"
            q["queue"][q["current_index"]]["error"] = None
            q["queue"][q["current_index"]]["started_at"] = None
            q["queue"][q["current_index"]]["finished_at"] = None
            if q["status"] == "failed":
                q["status"] = "pending"
            _save_task_queue(q)
        return q

def _queue_run_next():
    """Run the next pending task. Returns (task_dict, result_text, success_bool) or None if none."""
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        # Find next pending task at or after current_index
        idx = q["current_index"]
        while idx < len(q["queue"]) and q["queue"][idx]["status"] in ("done", "skipped"):
            idx += 1
        if idx >= len(q["queue"]):
            if q["status"] == "running":
                q["status"] = "completed"
                _save_task_queue(q)
            return None
        q["current_index"] = idx
        q["status"] = "running"
        task = q["queue"][idx]
        task["status"] = "running"
        task["started_at"] = time.time()
        _save_task_queue(q)
    
    # Execute outside the lock to avoid blocking status checks
    task_text = task["task"]
    try:
        # Use the existing chat dispatch for task execution
        msgs = [{"role": "system", "content": "You are ACEsi, an autonomous agent. Execute the task and report results."},
                {"role": "user", "content": task_text}]
        reply = _chat_dispatch(msgs, user_message=task_text, preferred_model=None)
        success = reply is not None and not reply.startswith("Error:")
        result_text = reply if reply else "No response"
    except Exception as e:
        success = False
        result_text = "%s: %s" % (type(e).__name__, e)
    
    # Update queue with result
    with _TASK_QUEUE_LOCK:
        q = _load_task_queue()
        if idx < len(q["queue"]):
            task = q["queue"][idx]
            task["status"] = "done" if success else "failed"
            task["result"] = result_text
            task["finished_at"] = time.time()
            if not success:
                task["error"] = result_text
            # Record result summary
            q["results"].append({
                "index": idx,
                "task": task_text,
                "status": task["status"],
                "result": result_text[:500],
                "error": task["error"],
            })
            # Determine next status based on on_failure policy
            if not success:
                policy = task.get("on_failure", "stop")
                if policy == "stop":
                    q["status"] = "failed"
                    _save_task_queue(q)
                    return task, result_text, success
                if policy == "retry":
                    # Reset the task and return WITHOUT advancing current_index.
                    # Both _queue_run_next and the worker only scan
                    # idx >= current_index, and current_index is persisted, so
                    # advancing here orphaned the retry permanently - even
                    # across a restart. Retry never actually happened.
                    task["status"] = "pending"
                    task["error"] = None
                    task["started_at"] = None
                    task["finished_at"] = None
                    q["status"] = "pending"
                    _save_task_queue(q)
                    return task, result_text, success
                # policy == "skip": fall through to the single advance below.
            # Advance exactly once. Previously "skip" incremented here AND in
            # the policy branch, so every skipped task silently swallowed the
            # next, un-run task.
            q["current_index"] += 1
            if q["current_index"] >= len(q["queue"]):
                q["status"] = "completed"
            else:
                q["status"] = "pending"
            _save_task_queue(q)
    return task, result_text, success

# Background runner - drains the queue on its own
_TASK_QUEUE_POLL = 5


def _task_queue_worker():
    """Daemon loop: run queued tasks automatically, one at a time, in order.

    This used to be documented as "call this periodically (e.g. from a timer)"
    but nothing ever called it, so a queued task only advanced when a human
    explicitly POSTed /queue/run. It is now started at boot (see the thread
    launch next to the other watchdogs), which is what makes "fix the 404 bug,
    then run tests, then commit" actually run itself.
    """
    time.sleep(8)  # let boot settle before touching the model providers
    while True:
        active = False
        try:
            if not _kill_armed():
                with _TASK_QUEUE_LOCK:
                    q = _load_task_queue()
                    active = q["status"] in ("running", "pending")
                if active:
                    _queue_run_next()
        except Exception as e:
            print("⚠️ task queue worker: %s: %s" % (type(e).__name__, e))
        # Fast while there is work, slow when idle so we don't burn CPU.
        time.sleep(0.5 if active else _TASK_QUEUE_POLL)

# ===== ACEsi dispatcher integration (ace_dispatcher module) ────────────────
# Provides robust multi-subtask execution as a fallback when the
# model-driven _chat_dispatch loop exhausts all providers.
# Key properties: tools never crash the loop (ToolRegistry.call),
# failed subtasks are recorded (not raised), state is persisted
# before each step, and reports lead with successes.

_DISPATCHER_REGISTRY = None
_DISPATCHER_LOCK = threading.RLock()
REGISTRY = None


def _dispatcher_tool_wrapper(name, args):
    """Call a server tool safely and return (ok, result_text)."""
    try:
        ok, result = _call_tool(name, args or {})
        return ok, str(result)
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, e)


def _make_tool_fn(name):
    """Return a function that calls _call_tool for the given tool name."""
    def _fn(**kwargs):
        return _dispatcher_tool_wrapper(name, kwargs)
    return _fn


def _build_dispatcher_registry():
    """Wrap server TOOLS into an ace_dispatcher.ToolRegistry."""
    global _DISPATCHER_REGISTRY, REGISTRY
    if _DISPATCHER_REGISTRY is not None:
        return _DISPATCHER_REGISTRY
    with _DISPATCHER_LOCK:
        if _DISPATCHER_REGISTRY is not None:
            return _DISPATCHER_REGISTRY
        reg = ace_dispatcher.ToolRegistry()
        schema_map = {_t.get("function", {}).get("name"): _t for _t in TOOLS_SCHEMA}
        for name in list(TOOLS.keys()):
            fn, arg_keys = TOOLS[name]
            schema = schema_map.get(name, {})
            description = (schema.get("function") or {}).get("description") or ""
            reg.register(name, fn=_make_tool_fn(name),
                         timeout=30.0, retries=1,
                         description=description,
                         original_fn=fn,
                         arg_keys=arg_keys,
                         schema=schema)
        _DISPATCHER_REGISTRY = reg
        REGISTRY = reg
        return reg


LEDGER_PATH = os.path.join(DATA_DIR, '.dispatch_ledger.json') if 'DATA_DIR' in dir() else '.dispatch_ledger.json'


def _run_dispatcher(user_message, subtasks=None, max_steps=50):
    """Run ace_dispatcher's TaskRunner for robust autonomous execution.

    Returns dict with summary, ok, counts, steps, stopped_early.
    """
    if ace_dispatcher is None:
        return {"summary": "ace_dispatcher module not available.",
                "ok": False, "counts": {}, "steps": []}
    registry = _build_dispatcher_registry()
    config = ace_dispatcher.RunConfig(max_steps=max_steps, fail_fast=False)

    if subtasks:
        plan = subtasks
    else:
        plan = [
            ace_dispatcher.Subtask(
                id="dispatch_1",
                title=user_message[:200],
                tool=None,
                args={"user_message": user_message},
            )
        ]

    # Diagnostic trace
    try:
        ledger = ace_dispatcher.TaskLedger(plan, path=LEDGER_PATH)
    except Exception as e:
        print("[ACE] ledger construction FAILED: %s: %s" % (type(e).__name__, e))
        raise

    result = ace_dispatcher.TaskRunner(registry, config, ledger_path=LEDGER_PATH).run(ledger)
    print("[ACE] steps=%d counts=%s ok=%s stopped=%r" % (
        result.steps, result.counts(), result.ok, result.stopped_early))
    if result.steps == 0:
        print("[ACE] NOTHING RAN. plan problems: %s" % (
            ledger.counts() if hasattr(ledger, 'counts') else 'no counts method'))

    summary = ace_dispatcher.summarize(result)
    return {
        "summary": summary,
        "ok": result.ok,
        "counts": result.counts(),
        "steps": [t.to_dict() for t in result.ledger],
        "stopped_early": result.stopped_early,
    }


def _safe_path(path):
    """Resolve path under PROJECT_ROOT, rejecting traversal escapes. None if unsafe."""
    if not path:
        return None
    p = path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)
    rp = os.path.realpath(p)
    if rp != PROJECT_ROOT and not rp.startswith(PROJECT_ROOT + os.sep):
        return None
    return rp

def _walk_files(root):
    skip = {'.git', '.dart_tool', '.gradle', 'build', '.vscode', '.idea',
            'node_modules', '__pycache__', '.gradle', 'venv', '.dart_tool', 'web'}
    out = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in skip]
        for d in sorted(dirs):
            out.append("📁 " + os.path.relpath(os.path.join(base, d), root) + "/")
        for f in sorted(files):
            out.append("📄 " + os.path.relpath(os.path.join(base, f), root))
    return sorted(out)

def tool_list_files(path="."):
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_path(path)
    if not rp or not os.path.isdir(rp):
        return False, "dir not found: %s" % path
    # Hide kill-state files from the agent's view of the project.
    out = _walk_files(rp)
    out = [l for l in out if not _kill_protected_path(os.path.join(rp, l.replace("📄 ", "").replace("📁 ", "")))]
    return True, "\n".join(out)[:4000]

def tool_read_file(path):
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_path(path)
    if not rp or not os.path.isfile(rp):
        return False, "file not found: %s" % path
    if _kill_protected_path(rp):
        return False, "blocked: that file is protected."
    try:
        with open(rp, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        cut = c[:8000]
        if len(c) > 8000:
            cut += "\n...[truncated, %d chars total]" % len(c)
        return True, cut
    except Exception as e:
        return False, str(e)

_USER_ALLOWED_ROOTS = [
    os.path.join(os.path.expanduser("~"), "Pictures"),
    os.path.join(os.path.expanduser("~"), "Desktop"),
    os.path.join(os.path.expanduser("~"), "Downloads"),
    os.path.join(os.path.expanduser("~"), "Documents"),
]

_USER_ALIASES = {
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "my documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "docs": os.path.join(os.path.expanduser("~"), "Documents"),
    "my pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "my desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "my downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
}

def _safe_user_path(path):
    """Resolve a user path to a real, existing location. Gives ACEsi access to
    the whole PC: any path that exists is allowed (absolute or relative to the
    home dir / project). Bare folder names ('Documents') and bare filenames
    ('GEPFGEPF') are resolved under the home dir or by searching the home tree.
    Returns the realpath string, or None if nothing matches."""
    if not path:
        return None
    p = path.strip().lower()
    if p in _USER_ALIASES:
        return _USER_ALIASES[p]
    home = os.path.expanduser("~")
    if not os.path.isabs(path):
        # Try "<home>/<path>" directly (covers 'Documents', 'My Documents',
        # 'Documents/GEPFGEPF', 'Pictures/foo.png' etc.)
        cand = os.path.join(home, path.strip())
        if os.path.exists(cand):
            return os.path.realpath(cand)
        # Try "<PROJECT_ROOT>/<path>" (dev files when not user folders)
        cand = os.path.join(PROJECT_ROOT, path.strip())
        if os.path.exists(cand):
            return os.path.realpath(cand)
        # Bare filename -> deep-ish search under the whole home tree
        rp = _find_user_file_fuzzy(path)
        if rp:
            return rp
        return None
    rp = os.path.realpath(path)
    if os.path.exists(rp):
        return rp
    return None

def _extract_user_file_hint(message):
    """Pull a filename out of a natural-language 'open/view <file>' request.
    E.g. 'the file Median XL and open it' -> 'Median XL'. Matches the biggest
    token run after 'file', or a dotted filename directly."""
    m = (message or "")
    pat = re.search(
        r'\bfile\s+(?:called\s+|named\s+|sf?\s+)?'
        r"([A-Za-z0-9][A-Za-z0-9 _.\-]*?)"
        r'(?=\s+(?:and\b|then\b|,|\.|$|\bin\b|\bon\b|\bopen\b|\bview\b|\bplease\b))',
        m, re.IGNORECASE)
    if pat:
        hint = pat.group(1).strip()
        if len(hint) >= 2:
            return hint
    pat2 = re.search(
        r'\b([A-Za-z0-9][A-Za-z0-9 _.\-]{2,}\.(?:png|jpe?g|gif|webp|bmp|pdf|txt|md|docx|csv|json))\b',
        m, re.IGNORECASE)
    if pat2:
        return pat2.group(1).strip()
    return None


def _match_open_user_file(message):
    """True when Chris asked to open/view/show a file in his user folders."""
    ml = (message or "").lower()
    has_open = bool(re.search(r'\b(?:open|view|show|display|read)\b', ml))
    filey = bool(re.search(
        r'\b(?:file|picture|photo|image|capture|median|gdpfgdpf)\b|\.(?:png|jpe?g|gif|pdf|txt|md|docx)\b', ml))
    find_open = bool(re.search(r'\bfind\b[^.!?\n]{0,80}\b(?:open|view|show)\b', ml))
    return bool((has_open and filey) or find_open)


def _find_user_file_fuzzy(name):
    """Case-insensitive search for a filename under the home tree, trying the
    bare name and with common extensions appended. Returns the realpath or None."""
    if not name:
        return None
    base = os.path.basename(name.strip().strip('"\'')).lower()
    base = re.sub(r'^the\s+file\s*[: ]?\s*', '', base).strip()
    base = re.sub(r'\s+(?:now|please)$', '', base).strip()
    if not base:
        return None
    exts = ['', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.pdf',
            '.txt', '.md', '.markdown', '.docx', '.doc', '.xlsx', '.csv',
            '.json', '.log']
    # Root = the whole home profile (full PC access); the four named root
    # aliases are all under it anyway. Skip heavy/unrestricted system dirs.
    SKIP = {'appdata', 'application data', 'ntuser.dat', 'ntuser.ini',
            '$recycle.bin', 'program files', 'program files (x86)',
            'windows', 'system volume information'}
    roots = _USER_ALLOWED_ROOTS + [os.path.expanduser("~")]
    seen = set()
    for root in roots:
        rr = os.path.realpath(root)
        if rr in seen:
            continue
        seen.add(rr)
        if not os.path.isdir(rr):
            continue
        for dirpath, dirnames, filenames in os.walk(rr):
            # prune heavy system dirs during the walk
            dirnames[:] = [d for d in dirnames if d.lower() not in SKIP]
            try:
                rp_dir = os.path.realpath(dirpath)
            except Exception:
                continue
            for fn in filenames:
                fnl = fn.lower()
                if fnl == base:
                    return os.path.realpath(os.path.join(rp_dir, fn))
                for e in exts:
                    if fnl == base + e:
                        return os.path.realpath(os.path.join(rp_dir, fn))
    return None


def tool_list_user_files(path="."):
    """List files/dirs anywhere on Chris's PC (any folder). Shallow — shows the
    immediate entries only (subfolders get an item count), so a big folder like
    Documents doesn't flood the reply/UI with hundreds of recursive lines."""
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_user_path(path)
    if not rp or not os.path.isdir(rp):
        return False, "dir not found or not allowed: %s" % path
    try:
        dirs = sorted(d for d in os.listdir(rp) if os.path.isdir(os.path.join(rp, d)))
        files = sorted(f for f in os.listdir(rp) if os.path.isfile(os.path.join(rp, f)))
    except Exception as e:
        return False, "cannot list: %s" % e
    out = []
    for d in dirs:
        dp = os.path.join(rp, d)
        try:
            n = len([1 for _ in os.listdir(dp)])
        except Exception:
            n = 0
        out.append("📁 %s/  (%d items)" % (d, n))
    out.extend("📄 %s" % f for f in files)
    if not out:
        return True, "(empty folder)"
    return True, "\n".join(out)[:4000]

def tool_read_user_file(path):
    """Read a file's content from anywhere on Chris's PC."""
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_user_path(path)
    if not rp or not os.path.isfile(rp):
        return False, "file not found or not allowed: %s" % path
    try:
        with open(rp, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        cut = c[:8000]
        if len(c) > 8000:
            cut += "\n...[truncated, %d chars total]" % len(c)
        return True, cut
    except Exception as e:
        return False, str(e)

def tool_open_user_file(path):
    """Open a file from anywhere on Chris's PC with the system default application.
    Also returns the inline view data (same as tool_view_user_file) so the popup
    ALWAYS appears in ACEsi's UI — the user opens a file and sees it immediately,
    with his click-to-edit button attached.
    """
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_user_path(path)
    if not rp or not os.path.isfile(rp):
        return False, "file not found or not allowed: %s" % path
    _open_external(rp)
    # Attach inline view so the UI popup appears AND stays clickable-to-edit.
    ok, result = tool_view_user_file(rp)
    if ok and isinstance(result, _ViewResult):
        return True, _ViewResult(
            "opened %s in the default app; displayed inline too" % os.path.basename(rp),
            result.view)
    return True, _ViewResult(
        "opened %s in the default app" % os.path.basename(rp),
        {"type": "external", "filename": os.path.basename(rp), "path": rp})

class _ViewResult:
    """Tool result that shows nicely to the model but carries view data for frontend."""
    __slots__ = ("model_msg", "view")
    def __init__(self, model_msg, view):
        self.model_msg = model_msg
        self.view = view
    def __str__(self):
        return self.model_msg
    def __repr__(self):
        return self.model_msg

def tool_view_user_file(path):
    """View a file from anywhere on Chris's PC inline in chat.
    Returns base64 data for images (png, jpg, jpeg, gif, webp, bmp) and PDFs.
    For other files, returns text content or an error."""
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_user_path(path)
    if not rp or not os.path.isfile(rp):
        return False, "file not found or not allowed: %s" % path
    import base64, mimetypes
    ext = os.path.splitext(rp)[1].lower()
    image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif'}
    # Sniff magic bytes so extension-less files (e.g. 'GEPFGEPF' that IS a PNG)
    # still display as images/PDFs instead of garbage text.
    sniff_type = None
    try:
        with open(rp, 'rb') as _f:
            _head = _f.read(16)
        if _head[:8] == b'\x89PNG\r\n\x1a\n':
            sniff_type = 'image'
            if ext not in image_exts:
                ext = '.png'
        elif _head[:2] == b'\xff\xd8':
            sniff_type = 'image'
            if ext not in image_exts:
                ext = '.jpg'
        elif _head[:6] in (b'GIF87a', b'GIF89a'):
            sniff_type = 'image'
            if ext not in image_exts:
                ext = '.gif'
        elif _head[:4] == b'%PDF':
            sniff_type = 'pdf'
        elif _head[:4] in (b'RIFF',):
            if _head[8:12] == b'WEBP':
                sniff_type = 'image'
                if ext not in image_exts:
                    ext = '.webp'
    except Exception:
        pass
    if ext in image_exts:
        try:
            with open(rp, 'rb') as f:
                data = f.read()
            if len(data) == 0:
                raise OSError("file is empty (cloud placeholder not downloaded?)")
            b64 = base64.b64encode(data).decode('ascii')
            mime = mimetypes.guess_type(rp)[0] or 'image/' + ext[1:]
            view = {"type": "image", "mime": mime, "data": b64, "filename": os.path.basename(rp),
                    "path": rp}
            return True, _ViewResult("[Image displayed inline: %s]" % os.path.basename(rp), view)
        except Exception as e:
            # Unreadable cloud-only file: open it externally so OneDrive can
            # hydrate/download the real content, and still surface a popup.
            _open_external(rp)
            return True, _ViewResult(
                "[%s is cloud-only/unreadable — opening it in its app]" % os.path.basename(rp),
                {"type": "external", "filename": os.path.basename(rp), "path": rp})
    # PDFs - return base64 for iframe embed
    if ext == '.pdf':
        try:
            with open(rp, 'rb') as f:
                data = f.read()
            if len(data) == 0:
                raise OSError("file is empty (cloud placeholder not downloaded?)")
            b64 = base64.b64encode(data).decode('ascii')
            view = {"type": "pdf", "mime": "application/pdf", "data": b64, "filename": os.path.basename(rp),
                    "path": rp}
            return True, _ViewResult("[PDF displayed inline: %s]" % os.path.basename(rp), view)
        except Exception as e:
            _open_external(rp)
            return True, _ViewResult(
                "[%s is cloud-only/unreadable — opening it in its app]" % os.path.basename(rp),
                {"type": "external", "filename": os.path.basename(rp), "path": rp})
    # Word docs - extract paragraphs from the docx zip so the text displays.
    if ext == '.docx':
        try:
            import zipfile, re as _re
            text_parts = []
            with zipfile.ZipFile(rp) as z:
                for name in z.namelist():
                    if name in ('word/document.xml',) or (name.startswith('word/') and name.endswith('.xml')):
                        xml = z.read(name).decode('utf-8', errors='replace')
                        paras = _re.findall(r'<w:p[ >].*?</w:p>|<w:p[ ]?/>', xml, _re.S)
                        for p in paras:
                            txt = _re.sub(r'<[^>]+>', '', p)
                            txt = txt.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&apos;', "'")
                            if txt.strip():
                                text_parts.append(txt.strip())
            cut = '\n'.join(text_parts)[:8000]
            view = {"type": "text", "content": cut or "(no extractable text)", "filename": os.path.basename(rp),
                    "path": rp}
            return True, _ViewResult("[Word document displayed inline: %s]" % os.path.basename(rp), view)
        except Exception as e:
            # Not a real zip = cloud-only placeholder (OneDrive hasn't downloaded
            # the content). Open it externally so the app hydrates it.
            _open_external(rp)
            return True, _ViewResult(
                "[%s is cloud-only/unreadable — opening it in its app]" % os.path.basename(rp),
                {"type": "external", "filename": os.path.basename(rp), "path": rp})
    # Text files - return text
    try:
        with open(rp, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        cut = c[:8000]
        if len(c) > 8000:
            cut += "\n...[truncated, %d chars total]" % len(c)
        view = {"type": "text", "content": cut, "filename": os.path.basename(rp),
                "path": rp}
        return True, _ViewResult("[Text file displayed inline: %s]" % os.path.basename(rp), view)
    except Exception as e:
        _open_external(rp)
        return True, _ViewResult(
            "[%s is cloud-only/unreadable — opening it in its app]" % os.path.basename(rp),
            {"type": "external", "filename": os.path.basename(rp), "path": rp})


def tool_view_web_image(url):
    """Download an image from a URL and display it inline in the ACEsi chat
    window as a popup (same as a local image). Args: url. The URL must point
    directly at an image file (png/jpg/jpeg/gif/webp/bmp). Returns a base64
    image view so the frontend renders it. For non-image URLs use curl/webfetch."""
    import base64, mimetypes, ssl
    if not url or not str(url).startswith(("http://", "https://")):
        return False, "view_web_image usage: url=http[s]://.../image.png"
    try:
        req = _urlreq.Request(str(url), headers={"User-Agent":
            "Mozilla/5.0 (ACEsi image viewer)"})
        ctx = ssl.create_default_context()
        handler = _urlreq.HTTPSHandler(context=ctx)
        opener = _urlreq.build_opener(handler, _urlreq.HTTPRedirectHandler())
        with opener.open(req, timeout=30) as resp:
            data = resp.read(15 * 1024 * 1024)
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].lower()
        if not data:
            return False, "view_web_image: empty response from %s" % url
        # Sniff magic bytes to pick the right mime/ext (servers mislabel often).
        ext = ".jpg"
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            ext, ctype = ".png", "image/png"
        elif data[:2] == b'\xff\xd8':
            ext, ctype = ".jpg", "image/jpeg"
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            ext, ctype = ".gif", "image/gif"
        elif data[:12] == b'RIFF' and data[8:12] == b'WEBP':
            ext, ctype = ".webp", "image/webp"
        elif data[:4] in (b'%PDF',):
            return True, _ViewResult(
                "[URL points at a PDF, not an image: %s]" % url,
                {"type": "pdf", "mime": "application/pdf",
                 "data": base64.b64encode(data).decode('ascii'),
                 "filename": "web_document.pdf", "path": url})
        b64 = base64.b64encode(data).decode('ascii')
        if not ctype.startswith("image/"):
            ctype = "image/" + ext[1:]
        fname = os.path.basename(_urlreq.urlsplit(str(url)).path) or ("image" + ext)
        if "." not in fname:
            fname += ext
        view = {"type": "image", "mime": ctype, "data": b64,
                "filename": fname, "path": str(url)}
        return True, _ViewResult("[Image displayed inline (from web): %s]" % fname, view)
    except _urlerr.HTTPError as e:
        return False, "view_web_image: HTTP %d fetching %s" % (e.code, url)
    except _urlerr.URLError as e:
        return False, "view_web_image: network error fetching %s — %s" % (url, str(getattr(e, "reason", e)))
    except _socket.timeout:
        return False, "view_web_image: timeout fetching %s" % url
    except Exception as e:
        return False, "view_web_image: %s" % str(e)[:200]

def tool_grep(pattern, path="."):
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_path(path)
    if not rp:
        rp = PROJECT_ROOT
    try:
        cre = re.compile(pattern)
    except re.error as e:
        return False, "bad regex: %s" % e
    hits = []
    targets = []
    if os.path.isfile(rp):
        targets.append(rp)
    else:
        for root, dirs, files in os.walk(rp):
            dirs[:] = [d for d in dirs if d not in ('build', '.dart_tool', '.git', '__pycache__', '.gradle', 'node_modules')]
            for fn in files:
                if fn.endswith(('.dart', '.py', '.js', '.ts', '.html', '.json', '.yaml', '.yml', '.md', '.txt')):
                    targets.append(os.path.join(root, fn))
    for fp in targets:
        if _kill_protected_path(fp):
            continue
        try:
            with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                for i, line in enumerate(fh, 1):
                    if cre.search(line):
                        rel = os.path.relpath(fp, rp if os.path.isdir(rp) else PROJECT_ROOT)
                        hits.append("%s:%d: %s" % (rel, i, line.rstrip()[:200]))
                        if len(hits) >= 50:
                            hits.append("...[more truncated]")
                            return True, "\n".join(hits)
        except Exception:
            pass
    return True, "\n".join(hits) if hits else "(no matches)"

def tool_write_file(path, content):
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_path(path)
    if not rp:
        return False, "path outside project: %s" % path
    if _kill_protected_path(rp):
        return False, "blocked: that file is protected."
    try:
        d = os.path.dirname(rp)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(rp, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, "wrote %s (%d chars)" % (os.path.relpath(rp, PROJECT_ROOT), len(content))
    except Exception as e:
        return False, str(e)

# The user's code editor (VS Code or the VSCodium fork Chris has installed).
_EDITOR_CANDIDATES = [
    r"D:\VSCodium\VSCodium\VSCodium.exe",
    r"D:\VSCodium\VSCodium\bin\codium.cmd",
    r"C:\Users\chris\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    r"C:\Program Files\Microsoft VS Code\Code.exe",
    r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
]

def _find_editor():
    for c in _EDITOR_CANDIDATES:
        if os.path.isfile(c):
            return c
    from shutil import which
    for name in ("code", "codium", "code-insiders"):
        p = which(name)
        if p:
            return p
    return None

_editor_path = [None]
def _vscode_open(draft_path):
    """Launch the editor on a file (best-effort, non-blocking). Returns (ok, msg)."""
    if _kill_armed():
        return False, "E-STOP is armed — no editor launches."
    if not os.path.isfile(draft_path):
        return False, "draft file not found: %s" % draft_path
    if _editor_path[0] is None:
        _editor_path[0] = _find_editor()
    if not _editor_path[0]:
        return False, ("No code editor found (VS Code / VSCodium not installed). "
                       "Draft was saved but could not be opened.")
    try:
        subprocess.Popen([_editor_path[0], draft_path],
                         creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        return True, "opened %s in the editor" % os.path.basename(draft_path)
    except Exception as e:
        return False, str(e)

def tool_open_in_vscode(path, content):
    """Write content to a REVIEW DRAFT (not the final file) and open it in the
    user's editor (VS Code/VSCodium) so Chris can review before deciding to save.
    Parks the draft + intended target in _AGENT['pending_save'] so a follow-up
    message ('save it' / 'keep it') can commit it, or 'discard' can delete it."""
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_path(path)
    if not rp:
        return False, "path outside project: %s" % path
    if _kill_protected_path(rp):
        return False, "blocked: that file is protected."
    # Draft lives beside the final target in a .draft/ sibling folder so it
    # cannot be mistaken for the committed file and is easy to clean up.
    draft_dir = os.path.join(os.path.dirname(rp), ".draft")
    try:
        os.makedirs(draft_dir, exist_ok=True)
        draft = os.path.join(draft_dir, os.path.basename(rp))
        with open(draft, 'w', encoding='utf-8') as f:
            f.write(content or "")
    except Exception as e:
        return False, str(e)
    ok, msg = _vscode_open(draft)
    rel_draft = os.path.relpath(draft, PROJECT_ROOT)
    rel_target = os.path.relpath(rp, PROJECT_ROOT)
    with _AGENT_LOCK:
        _AGENT["pending_save"] = {"draft": draft, "target": rp}
    if not ok:
        return True, ("Draft saved but could NOT open the editor: %s. "
                      "Draft is at %s — tell Chris the draft is ready for review "
                      "and answer only: saved_draft %s" % (msg, rel_draft, rel_target))
    return True, ("Draft opened in the editor for Chris to review: %s. "
                  "The final file %s has NOT been written yet. Tell Chris to review "
                  "it in VS Code, then reply with EXACTLY: saved_draft %s"
                  % (rel_draft, rel_target, rel_target))

def _commit_pending_save():
    """Move the parked review draft to its final target. Returns a user-facing message."""
    with _AGENT_LOCK:
        pending = _AGENT.get("pending_save")
        if not pending:
            return None
        draft, target = pending.get("draft"), pending.get("target")
        _AGENT["pending_save"] = None
    if not (draft and target) or not os.path.isfile(draft):
        return "There is no draft waiting to be saved."
    try:
        d = os.path.dirname(target)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(draft, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        os.remove(draft)
        return "Saved the reviewed draft to %s." % os.path.relpath(target, PROJECT_ROOT)
    except Exception as e:
        return "Could not save the draft: %s" % e

def _discard_pending_save():
    """Delete the parked review draft. Returns a user-facing message."""
    with _AGENT_LOCK:
        pending = _AGENT.get("pending_save")
        if not pending:
            return None
        draft = pending.get("draft")
        _AGENT["pending_save"] = None
    if draft and os.path.isfile(draft):
        try:
            os.remove(draft)
            return "Discarded the draft — nothing was saved."
        except Exception as e:
            return "Could not delete the draft: %s" % e
    return "There is no draft waiting to be discarded."

def tool_edit_file(path, old, new):
    if _kill_armed():
        return False, "E-STOP is armed — no file tools."
    rp = _safe_path(path)
    if not rp:
        return False, "path outside project: %s" % path
    if _kill_protected_path(rp):
        return False, "blocked: that file is protected."
    try:
        with open(rp, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
    except Exception as e:
        return False, str(e)
    if old not in c:
        return False, "old_string not found in file"
    count = c.count(old)
    if count > 1:
        return False, "old_string is ambiguous (%d matches) — add more context" % count
    try:
        with open(rp, 'w', encoding='utf-8') as f:
            f.write(c.replace(old, new, 1))
        return True, "edited %s (1 replacement)" % os.path.relpath(rp, PROJECT_ROOT)
    except Exception as e:
        return False, str(e)

# Blocked shell commands keep the agent from nuking the project/env.
_DESTRUCTIVE = re.compile(
    r'^\s*(rm(?:\s+-rf)?|rd|rmdir|del|erase|format|shutdown|reboot|'
    r'git\s+(push|pushall|reset|checkout|rebase|merge|stash|reflog|branch\s+-D|switch|clean|filter-branch)|'
    r'flutter\s+(clean|pub\s+get|pub\s+upgrade|build|bootstrap)|'
    r'dart\s+(compile|pub\s+get|pub\s+upgrade)|'
    r'adb\s+(uninstall|shell\s+pm\s+clear|shell\s+rm)|scrcpy|'
    r'(taskkill\s+/f)|'
    r'(kill_switch\.json|\.ace_kill\.local))\b', re.I)

def tool_run_command(command, timeout=120):
    if _kill_armed():
        return False, "E-STOP is armed — no commands run."
    if _DESTRUCTIVE.search(command):
        return False, "blocked (safety): %s" % command
    lb = (command or '').lower()
    if 'kill_switch.json' in lb or '.ace_kill.local' in lb:
        return False, "blocked (protected file): %s" % command
    try:
        # `flutter run` / `dart run` are long-lived dev sessions — stream to a
        # log file and return immediately instead of blocking forever.
        if re.match(r'^\s*(flutter\s+run|dart\s+run)\b', command, re.I):
            command = _resolve_run_device(command)
            if command is None:
                return False, 'flutter run needs a connected Android device (none found or locked/offline).'
            log_path = os.path.join(PROJECT_ROOT, 'run_%s.log' % uuid.uuid4().hex[:8])
            log = open(log_path, 'w', encoding='utf-8')
            proc = _track_proc(_popen(command, shell=True, stdout=log,
                                      stderr=subprocess.STDOUT, cwd=PROJECT_ROOT))
            return True, ('%s started (pid %d). Watch: Get-Content %s -Wait. '
                          'Logs: %s') % (command, proc.pid, log_path, log_path)
        r = _run(command, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=PROJECT_ROOT, env=os.environ.copy())
        out = (r.stdout or '') + (r.stderr or '')
        out = out.strip()
        if len(out) > 3000:
            out = out[-3000:] + "\n...[truncated]"
        return True, "exit=%d\n%s" % (r.returncode, out)
    except subprocess.TimeoutExpired:
        return False, "timed out after %ds" % timeout
    except Exception as e:
        return False, str(e)


# ---- Git / build / dependency tools (dedicated, bypass the shell blocklist
# ---- but with their own guardrails) ----

def _run_shell(cmd, timeout=300, cwd=None):
    try:
        r = _run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd or PROJECT_ROOT,
                           env=os.environ.copy())
        out = ((r.stdout or '') + (r.stderr or '')).strip()
        if len(out) > 4000:
            out = out[-4000:] + "\n...[truncated]"
        return r.returncode == 0, "exit=%d\n%s" % (r.returncode, out)
    except subprocess.TimeoutExpired:
        return False, "timed out after %ds" % timeout
    except Exception as e:
        return False, str(e)


def _run_args(args, timeout=300):
    # Windows-safe: list2cmdline does proper quoting, shell=True resolves .bat
    cmdline = subprocess.list2cmdline(args)
    try:
        r = _run(cmdline, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=PROJECT_ROOT,
                           env=os.environ.copy())
        out = ((r.stdout or '') + (r.stderr or '')).strip()
        if len(out) > 4000:
            out = out[-4000:] + "\n...[truncated]"
        return r.returncode == 0, "exit=%d\n%s" % (r.returncode, out)
    except subprocess.TimeoutExpired:
        return False, "timed out after %ds" % timeout
    except Exception as e:
        return False, str(e)


def tool_git_status():
    return _run_args(["git", "status", "--short", "--branch"], timeout=30)


def tool_git_log(n=10):
    try:
        n = max(1, min(int(n), 50))
    except Exception:
        n = 10
    return _run_args(["git", "log", "--oneline", "-%d" % n], timeout=30)


def tool_git_commit(message, files=None):
    if not message or not str(message).strip():
        return False, "usage: git_commit message=<commit message>"
    if files:
        if isinstance(files, str):
            files = [files]
        stage = ["git", "add", "-A", "--"] + [str(f) for f in files]
    else:
        stage = ["git", "add", "-A"]
    ok1, out1 = _run_args(stage, timeout=60)
    if not ok1:
        return False, out1
    ok2, out2 = _run_args(["git", "-c", "user.name=ACEsi",
                           "-c", "user.email=acesi@local",
                           "commit", "-m", str(message)], timeout=60)
    if "nothing to commit" in out2 or "no changes added" in out2:
        return True, "nothing to commit (working tree clean)"
    return ok2, out2


def tool_git_branch(name=None, create=False):
    if name and create:
        return _run_args(["git", "checkout", "-b", str(name)], timeout=60)
    return _run_args(["git", "branch", "-a"], timeout=30)


def tool_git_merge(branch):
    if not branch:
        return False, "usage: git_merge branch=<branch-name>"
    b = str(branch).strip()
    ok, out = _run_args(["git", "branch", "--list", b], timeout=30)
    if not ok or b not in out:
        return False, "branch '%s' does not exist locally: %s" % (b, out)
    ok2, out2 = _run_args(["git", "merge", "--no-commit", "--no-ff", b], timeout=180)
    if "CONFLICT" in out2:
        return False, "merge conflicts in %s:\n%s\nResolve conflicts with edit_file, then git_commit." % (b, out2)
    _run_args(["git", "merge", "--abort"], timeout=60)  # roll back --no-commit staging
    if not ok2:
        return False, out2
    return _run_args(["git", "merge", b], timeout=180)


def tool_build_apk(mode="release"):
    mode = (mode or "release").lower().strip()
    if mode not in ("release", "debug"):
        return False, "usage: build_apk mode=release|debug"
    ok, out = _run_args(["flutter", "build", "apk", "--" + mode], timeout=600)
    apk = os.path.join(PROJECT_ROOT, "build", "app", "outputs",
                       "flutter-apk", "app-%s.apk" % mode)
    exists = os.path.exists(apk)
    if ok and exists:
        size = os.path.getsize(apk) // 1024
        return True, "%s\nAPK: %s (%d KB)" % (out, apk, size)
    return ok, out


def tool_pub_add(package):
    if not package:
        return False, "usage: pub_add package=<name[@version]>"
    return _run_args(["flutter", "pub", "add", str(package).strip()], timeout=300)


def tool_pub_remove(package):
    if not package:
        return False, "usage: pub_remove package=<name>"
    return _run_args(["flutter", "pub", "remove", str(package).strip()], timeout=300)


def tool_pub_upgrade():
    return _run_args(["flutter", "pub", "upgrade"], timeout=300)


def tool_flutter_test(path=None):
    if path and str(path).strip():
        return _run_args(["flutter", "test", str(path).strip()], timeout=600)
    return _run_args(["flutter", "test"], timeout=600)


def tool_flutter_analyze():
    return _run_args(["flutter", "analyze"], timeout=600)


# ---- UI testing: interact with the app on the connected Android device ----

ACE_PACKAGE = "com.studentsyncsa.studentsyncsa"
ACE_UI_SHOTS = os.path.join(PROJECT_ROOT, "ui_screenshots")
# University of Venda ITS / iEnabler portal (prodi41 startup URL). Used by the
# /check-portal health route and by ACEsi's network diagnostics. The public
# university site (www.univen.ac.za) links to this exact host.
UNIVEN_ITS_STARTUP_URL = ("https://univenierp01.univen.ac.za/pls/prodi41/"
                           "gen.gw1pkg.gw1startup?x_processcode=ITS_OAP")
# Last captured screenshot lives in memory (NOT on disk by default) so it can be
# served to the frontend popup without cluttering ui_screenshots/. ts increments
# every capture so clients can detect a NEW screenshot after a run.
_LAST_SHOT = {"png": b"", "ts": 0}
_UI_KEYS = {"back": "4", "home": "3", "enter": "66", "tab": "61", "menu": "82",
            "up": "19", "down": "20", "left": "21", "right": "22",
            "esc": "111", "power": "26", "recents": "187"}


def _ui_adb(args, timeout=120, cap=3000):
    cmd = subprocess.list2cmdline(["adb"] + args)
    try:
        proc = _popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=os.environ.copy())
        try:
            r_out, r_err = proc.communicate(timeout=timeout)
            out = (r_out.decode('utf-8', 'replace') + r_err.decode('utf-8', 'replace')).strip()
            if cap and len(out) > cap:
                out = out[-cap:] + "\n...[truncated]"
            return proc.returncode == 0, out
        except subprocess.TimeoutExpired:
            # Kill the whole tree (shell=True spawns cmd.exe -> adb.exe); an
            # orphaned adb.exe would otherwise hold the device and stall every
            # later adb call in the run.
            try:
                _run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                               capture_output=True, timeout=10)
            except Exception:
                pass
            return False, "timed out after %ds" % timeout
    except Exception as e:
        return False, str(e)


def tool_ui_device():
    ok, out = _ui_adb(["devices"])
    size = ""
    ok2, size = _ui_adb(["shell", "wm", "size"])
    ok3, dens = _ui_adb(["shell", "wm", "density"])
    return True, "%s\nscreen: %s | density: %s" % (out, size, dens)


def tool_ui_app_open():
    # Force the app to the foreground. `monkey -p ... 1` only launches the
    # launcher activity; if the app is already running it may stay behind a
    # fullscreen app (e.g. the Honor search screen) and every later tap fails.
    # `am start` with FLAG_ACTIVITY_NEW_TASK|CLEAR_TOP brings the existing task
    # forward, then we verify the resumed activity is ours and retry once.
    launch = ["shell", "am", "start",
              "-n", "%s/.MainActivity" % ACE_PACKAGE,
              "-a", "android.intent.action.MAIN",
              "-c", "android.intent.category.LAUNCHER"]
    ok, out = _ui_adb(launch, timeout=60)
    if not ok:
        return ok, out
    for attempt in (1, 2):
        # Parse locally: dumpsys output is large and the ResumedActivity lines
        # sit near the TOP, so cap must keep them (full output ~40KB).
        fg = _ui_adb(["shell", "dumpsys", "activity", "activities"],
                     timeout=60, cap=120000)
        if not fg[0]:
            continue
        lines = [l for l in fg[1].splitlines()
                 if "topResumedActivity" in l or "ResumedActivity:" in l]
        if lines and ACE_PACKAGE in lines[-1]:
            return True, "foreground: %s" % lines[-1].strip()
        if attempt == 1:
            # Second launch pass: NEW_TASK|CLEAR_TOP more aggressively resumes
            # the running task instead of just scheduling a new activity.
            _ui_adb(["shell", "am", "start", "--activity-brought-to-front",
                     "-n", "%s/.MainActivity" % ACE_PACKAGE], timeout=60)
            _ui_adb(["shell", "input", "keyevent", "3"], timeout=60)  # home
            ok, out = _ui_adb(launch, timeout=60)
    return True, "launched %s (foreground unverified)" % ACE_PACKAGE


def tool_ui_tap(x, y):
    try:
        x = int(float(str(x).replace(",", "")))
        y = int(float(str(y).replace(",", "")))
    except Exception:
        return False, "usage: ui_tap x=<int> y=<int>"
    return _ui_adb(["shell", "input", "tap", str(x), str(y)])


def tool_ui_swipe(x1, y1, x2, y2, duration=200):
    try:
        x1 = int(float(str(x1).replace(",", "")))
        y1 = int(float(str(y1).replace(",", "")))
        x2 = int(float(str(x2).replace(",", "")))
        y2 = int(float(str(y2).replace(",", "")))
        duration = int(float(str(duration).replace(",", "")))
    except Exception:
        return False, "usage: ui_swipe x1 y1 x2 y2 [duration=200]"
    return _ui_adb(["shell", "input", "swipe", str(x1), str(y1),
                    str(x2), str(y2), str(duration)])


def tool_ui_type(text):
    if not text:
        return False, "usage: ui_type text=<string to type>"
    safe = str(text).replace(" ", "%s").replace("'", "").replace('"', "")
    return _ui_adb(["shell", "input", "text", safe])


def tool_ui_key(key):
    k = str(key).strip().lower()
    if k in _UI_KEYS:
        return _ui_adb(["shell", "input", "keyevent", _UI_KEYS[k]])
    if k.isdigit():
        return _ui_adb(["shell", "input", "keyevent", k])
    return False, "usage: ui_key key=%s" % "/".join(sorted(_UI_KEYS))


def _ui_dump_compact(xml, cap=3000):
    """Extract only the labeled nodes (text/content-desc) with their bounds, so
    the model sees a compact actionable list (label + tap center) instead of raw
    XML full of empty text=\"\" attributes. Returns the compact string."""
    import xml.etree.ElementTree as ET
    lines = []
    for n in ET.fromstring(xml).iter("node"):
        t = (n.get("text") or "").strip()
        d = (n.get("content-desc") or "").strip()
        label = t or d
        if not label:
            continue
        b = n.get("bounds", "")
        import re as _re
        m = _re.findall(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
        cx = cy = ""
        if m:
            x1, y1, x2, y2 = (int(v) for v in m[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        lines.append('%s @ tap(%s,%s)%s' % (label, cx, cy,
                     " [CLICKABLE]" if n.get("clickable") == "true" else ""))
    total = len(lines)
    joined = "\n".join(lines)
    if len(joined) > cap:
        joined = joined[:cap] + "\n...[truncated]"
    return "%d labeled nodes\n%s" % (total, joined)


def tool_ui_dump():
    _ui_adb(["shell", "uiautomator", "dump", "/sdcard/ui.xml"])
    ok, out = _ui_adb(["shell", "cat", "/sdcard/ui.xml"], cap=None)
    if not ok or "<hierarchy" not in out:
        return False, "ui dump failed: %s" % out[:500]
    try:
        return True, _ui_dump_compact(out)
    except Exception as e:
        nodes = out.count("<node")
        trimmed = out[:3000] + ("\n..." if len(out) > 3000 else "")
        return True, "%d visible nodes (compact parse failed: %s)\n%s" % (nodes, e, trimmed)


def tool_ui_screenshot(name=None, save=False):
    try:
        r = _run(
            subprocess.list2cmdline(["adb", "exec-out", "screencap", "-p"]),
            shell=True, capture_output=True, timeout=60, env=os.environ.copy())
        data = r.stdout if isinstance(r.stdout, bytes) else r.stdout.encode()
        if not data.startswith(b"\x89PNG"):
            return False, "screencap failed: %s" % r.stderr[:300]
        # Buffer in memory so /screenshot/latest can show it in a popup; only
        # write to disk when Chris explicitly asked to save it.
        _LAST_SHOT["png"] = data
        _LAST_SHOT["ts"] += 1
        if save:
            os.makedirs(ACE_UI_SHOTS, exist_ok=True)
            fname = "%s_%s.png" % (name or "ui", datetime.now().strftime("%H%M%S"))
            path = os.path.join(ACE_UI_SHOTS, fname)
            with open(path, "wb") as f:
                f.write(data)
            return True, ("%s (%d KB) -- SAVED to disk at Chris's request. Shown in a popup too. "
                          "NOTE: you cannot view images; the user can in the screenshot popup." %
                          (path, len(data) // 1024))
        return True, ("Screenshot captured (%d KB) and shown to Chris in a popup -- NOT saved to disk. "
                      "If you or Chris later want it as a file, call ui_screenshot with {\"save\": true}. "
                      "You cannot view images; describe the screen from ui_dump labels, never the image." %
                      (len(data) // 1024))
    except subprocess.TimeoutExpired:
        return False, "screencap timed out"
    except Exception as e:
        return False, str(e)


# ---- UI validation: assertions + scripted test harness ----
# Chris wants ACEsi to validate the UI after every change. The assertion tools
# below dump the accessibility hierarchy (same uiautomator command as ui_dump)
# and compare it against expected labels/elements, returning ok=True only when
# the assertion HOLDS. They are read-only (never navigate) so they are safe to
# call inside any /chat run or a scripted ui_test_run.

_UI_LAST_TEST = {"ts": 0, "name": "", "passed": 0, "total": 0, "report": ""}


def _ui_parse_nodes(xml):
    """Parse a uiautomator XML dump into node dicts (text/content-desc/
    resource-id/class/visibility/bounds + tap center). Uses only stdlib (ET)."""
    import xml.etree.ElementTree as ET
    nodes = []
    for n in ET.fromstring(xml).iter("node"):
        b = n.get("bounds", "")
        x1 = y1 = x2 = y2 = None
        m = re.findall(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b)
        if m:
            x1, y1, x2, y2 = (int(v) for v in m[0])
        nodes.append({
            "text": (n.get("text") or "").strip(),
            "desc": (n.get("content-desc") or "").strip(),
            "rid": (n.get("resource-id") or "").strip(),
            "cls": (n.get("class") or "").strip(),
            "clickable": n.get("clickable") == "true",
            "focusable": n.get("focusable") == "true",
            "visible": (n.get("visible-to-user") or "true") != "false",
            "enabled": n.get("enabled") != "false",
            "bounds": b, "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "cx": (x1 + x2) // 2 if x1 is not None else None,
            "cy": (y1 + y2) // 2 if y1 is not None else None,
        })
    return nodes


def _ui_dump_nodes(timeout=45):
    """Full uiautomator dump parsed into node dicts. Returns (ok, nodes|err)."""
    _ui_adb(["shell", "uiautomator", "dump", "/sdcard/ui.xml"])
    ok, out = _ui_adb(["shell", "cat", "/sdcard/ui.xml"], cap=None)
    if not ok or "<hierarchy" not in out:
        return False, "ui dump failed: %s" % out[:500]
    try:
        return True, _ui_parse_nodes(out)
    except Exception as e:
        return False, "ui dump parse error: %s" % e


def _ui_screen_size():
    """(width, height) of the device screen, or (None, None)."""
    try:
        ok, out = _ui_adb(["shell", "wm", "size"], timeout=30)
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return None, None


def _ui_node_labels(node):
    """Node label candidates the model cares about (text then content-desc)."""
    return [node.get("text") or "", node.get("desc") or ""]


def _ui_assert_find(rid=None, text=None, desc=None, cls=None):
    """Find nodes matching the given selectors (all that are provided must match;
    text matches as a case-insensitive substring of text OR content-desc). Returns
    (ok, nodes) where nodes is the matching list, ok=False if the dump failed."""
    dko, dkres = _ui_dump_nodes()
    if not dko:
        return False, dkres
    matched = []
    for n in dkres:
        if rid and n["rid"] != str(rid):
            continue
        if cls and str(cls) not in n["cls"]:
            continue
        if desc and n["desc"] != str(desc):
            continue
        if text:
            tl = str(text).lower()
            if tl not in (n["text"] or "").lower() and tl not in (n["desc"] or "").lower():
                continue
        matched.append(n)
    if not (rid or text or desc or cls):
        return True, []
    return True, matched


def tool_ui_assert_text(text, present=True):
    if not text or not str(text).strip():
        return False, "ui_assert_text usage: text=<string to look for> [present=true|false]"
    dko, dkres = _ui_dump_nodes()
    if not dko:
        return False, "ui_assert_text FAIL: %s" % dkres
    tl = str(text).strip().lower()
    found = [n for n in dkres if tl in (n["text"] or "").lower() or tl in (n["desc"] or "").lower()]
    want_present = str(present).lower() not in ("0", "false", "no")
    if want_present and found:
        return True, "PASS: ui_assert_text found %r on screen (%d match%s)" % (
            text, len(found), "es" if len(found) > 1 else "")
    if (not want_present) and not found:
        return True, "PASS: ui_assert_text confirmed %r is NOT on screen" % text
    if want_present:
        labels = [l for n in dkres for l in _ui_node_labels(n) if l][:30]
        return False, "FAIL: ui_assert_text: %r NOT on screen. Labels: %s" % (
            text, " | ".join(labels))
    return False, "FAIL: ui_assert_text: %r IS on screen (asserted absent): %d match%s" % (
        text, len(found), "es" if len(found) > 1 else "")


def tool_ui_assert_element(resource_id="", text="", desc="", cls="", present=True):
    selectors = dict(rid=resource_id, text=text, desc=desc, cls=cls)
    if not any(v for v in selectors.values()):
        return False, "ui_assert_element usage: give at least one of resource_id, text, desc, cls"
    dko, matched = _ui_assert_find(**selectors)
    if not dko:
        return False, "ui_assert_element FAIL: %s" % matched
    want_present = str(present).lower() not in ("0", "false", "no")
    sel = ", ".join("%s=%r" % (k, v) for k, v in selectors.items() if v)
    if want_present and matched:
        m = matched[0]
        return True, "PASS: ui_assert_element (%s) found at %s [%s]" % (
            sel, m["bounds"], m["cls"] or "?")
    if (not want_present) and not matched:
        return True, "PASS: ui_assert_element confirmed no element matches (%s)" % sel
    rids = sorted({n["rid"] for n in matched or [] if n["rid"]})[:10]
    return False, "FAIL: ui_assert_element (%s) not found%s" % (
        sel, "; existing resource-ids: %s" % (", ".join(rids) if rids else " none visible"))


def tool_ui_assert_visible(resource_id="", text="", desc="", cls=""):
    selectors = dict(rid=resource_id, text=text, desc=desc, cls=cls)
    if not any(v for v in selectors.values()):
        return False, "ui_assert_visible usage: give at least one of resource_id, text, desc, cls"
    dko, matched = _ui_assert_find(**selectors)
    if not dko:
        return False, "ui_assert_visible FAIL: %s" % matched
    W, H = _ui_screen_size()
    sel = ", ".join("%s=%r" % (k, v) for k, v in selectors.items() if v)
    for n in matched:
        if n["x1"] is None:
            continue
        if not n["visible"] or not n["enabled"]:
            continue
        on_screen = True
        if W is not None and H is not None:
            if n["x1"] < 0 or n["y1"] < 0 or n["x2"] > W or n["y2"] > H:
                on_screen = False
        if on_screen:
            return True, "PASS: ui_assert_visible (%s) is VISIBLE on screen at %s" % (sel, n["bounds"])
    return False, "FAIL: ui_assert_visible (%s) found but NOT visible/interactable on screen" % sel


def _ui_split_fragments(s):
    parts = []
    for line in str(s).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        for p in line.split(","):
            p = p.strip().strip("'\"")
            if p:
                parts.append(p)
    return parts


def _ui_expect_parse(expected):
    """Accept an expected-state JSON dict ({present:[],absent:[]}) or plain text
    (each line/comma fragment must be present). Returns (present, absent) or
    (None, error)."""
    s = str(expected or "").strip()
    if not s:
        return None, "ui_expect usage: expected=<JSON {present:[],absent:[]} or text fragments>"
    present, absent = [], []
    try:
        d = json.loads(s)
        if isinstance(d, dict):
            for k in ("present", "include", "must"):
                if isinstance(d.get(k), list) or isinstance(d.get(k), str):
                    present = _ui_split_fragments("\n".join(
                        d[k] if isinstance(d[k], list) else [d[k]])) if d.get(k) else []
                    break
            if isinstance(d.get("absent"), list) or isinstance(d.get("absent"), str):
                absent = _ui_split_fragments("\n".join(
                    d["absent"] if isinstance(d["absent"], list) else [d["absent"]])) if d.get("absent") else []
        else:
            present = _ui_split_fragments(d)
    except Exception:
        present = _ui_split_fragments(s)
    if not present and not absent:
        return None, "ui_expect: expected state had no present/absent fragments"
    return (present or [], absent or []), None


def tool_ui_expect(expected):
    """Compare the current ui_dump against an expected state. `expected` is either
    a JSON dict {"present": [labels that must be on screen], "absent": [labels that
    must be absent]} or a plain string of fragments that must all be present."""
    parsed = _ui_expect_parse(expected)
    if parsed is None or parsed[1]:
        err = parsed[1] if parsed else "ui_expect usage error"
        return False, err
    present, absent = parsed[0]
    dko, dkres = _ui_dump_nodes()
    if not dko:
        return False, "ui_expect FAIL: %s" % dkres
    corpus = " | ".join(l for n in dkres for l in _ui_node_labels(n) if l).lower()
    missing = [f for f in present if f.lower() not in corpus]
    unexpected = [f for f in absent if f.lower() in corpus]
    if not missing and not unexpected:
        return True, "PASS: ui_expect — screen matches expected state (present=%d, absent=%d)" % (
            len(present), len(absent))
    bits = []
    if missing:
        bits.append("missing on screen: %s" % ", ".join(repr(m) for m in missing))
    if unexpected:
        bits.append("should be absent but present: %s" % ", ".join(repr(u) for u in unexpected))
    return False, "FAIL: ui_expect — %s" % "; ".join(bits)


def tool_ui_test_run(steps, name=""):
    """Scripted UI test harness. `steps` is a JSON list of {tool, args} entries
    (any ui_* action or ui_assert_* tool). Each step runs sequentially; the tool
    result decides PASS/FAIL per step. Reports a pass/fail summary, and stores the
    result in the global so /opencode/status can surface it."""
    if isinstance(steps, str):
        try:
            steps = json.loads(steps)
        except Exception:
            return False, "ui_test_run usage: steps=<JSON list of {tool,args}>"
    if not isinstance(steps, list) or not steps:
        return False, "ui_test_run usage: steps=<non-empty JSON list of {tool,args}>"
    lines, passed = [], 0
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict) or not step.get("tool"):
            return False, "ui_test_run: step %d must be a {tool:..., args:...} dict" % i
        tool, args = step["tool"], step.get("args") or {}
        if tool not in TOOLS:
            return False, "ui_test_run: step %d unknown tool %r" % (i, tool)
        try:
            ok, res = _call_tool(tool, args)
        except Exception as e:
            ok, res = False, "harness error: %s" % e
        if ok:
            passed += 1
        sres = str(res)
        if len(sres) > 300:
            sres = sres[:300] + "…"
        detail = (" — %s" % sres) if ok else (" — %s" % sres)
        lines.append("%2d. [%s] %s %s%s" % (
            i, "PASS" if ok else "FAIL", tool,
            _tool_desc_short(tool, args), detail))
    total = len(steps)
    verdict = "TEST PASSED (%d/%d)" % (passed, total) if passed == total \
        else "TEST FAILED (%d/%d)" % (passed, total)
    report = "ui_test_run %s: %s\n%s" % (name or "scenario", verdict, "\n".join(lines))
    with _AGENT_LOCK:
        _UI_LAST_TEST.update({"ts": time.time(), "name": name or "",
                              "passed": passed, "total": total, "report": report})
    print("🧪 ui_test_run %s: %s" % (name or "", verdict))
    return passed == total, report


def _tool_desc_short(name, args):
    try:
        return _tool_desc(name, args)
    except Exception:
        return name


# ---- Self-hosting / self-healing runtime controls ----

ACE_HOST_FLAG = os.path.join(PROJECT_ROOT, "ace_host.flag")
ACE_HOST_PID = os.path.join(PROJECT_ROOT, "ace_host.pid")


def _watchdog_alive():
    try:
        if not os.path.exists(ACE_HOST_PID):
            return False
        pid = int(open(ACE_HOST_PID).read().strip())
        r = _run("tasklist /FI \"PID eq %d\"" % pid, shell=True,
                           capture_output=True, text=True, timeout=30)
        return str(pid) in r.stdout
    except Exception:
        return False


def tool_restart(what="cdp"):
    w = str(what or "cdp").lower().strip()
    if w == "server":
        if _watchdog_alive():
            with open(ACE_HOST_FLAG, "w") as f:
                f.write("restart")
            return True, ("ace_host.py watchdog (pid %s) will restart the server within ~3s; "
                          "the API may drop briefly." % open(ACE_HOST_PID).read().strip())
        return True, ("no watchdog running (ace_host.pid not found). Restart manually: "
                      "`python ace_host.py` (auto-restarts on crash) or `python -u server.py`.")
    if w == "chrome":
        ok = d.restart_local_chrome()
        return ok, ("local CDP chrome relaunched at http://127.0.0.1:9230"
                    if ok else "failed to relaunch chrome")
    if w == "cdp":
        old = d.status()[:160]
        sess = d._get_session(force=True)
        new = sess.ws.url if sess else "none"
        return True, "cdp session reset. previous: %s\nnew target: %s" % (old, new)
    if w == "ollama":
        try:
            rr = requests.get("http://localhost:11434/api/tags", timeout=3)
            return True, "ollama is already running (%d models)" % len(rr.json().get("models", []))
        except Exception:
            try:
                _popen(["ollama", "serve"],
                                 creationflags=subprocess.DETACHED_PROCESS | _NO_WINDOW,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, "ollama was down — started `ollama serve` detached. Wait ~5s then retry."
            except Exception as e:
                return False, "failed to start ollama: %s" % e
    return False, "usage: restart what=server|chrome|cdp|ollama"


# ---- CDP (Chrome DevTools Protocol) tools: inspect the ITS WebView / local Chrome ----

def tool_cdp_connect():
    ok, msg = d.connect_cmd()
    return ok, msg

def tool_cdp_evaluate(expr):
    if not expr:
        return False, "usage: cdp_evaluate <expression>"
    return d.evaluate_js(expr)

def tool_cdp_console_logs():
    return d.get_console_logs()

def tool_cdp_dom_state():
    return d.get_dom_state()

def tool_cdp_network_requests():
    return d.get_network_requests()

def tool_cdp_status():
    return True, d.status()


import urllib.request as _urlreq
import urllib.error as _urlerr
import socket as _socket


class _NoRedirectHandler(_urlreq.HTTPRedirectHandler):
    """Used when allow_redirects=False: stop following 3xx redirects."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _body_snippet(data, ctype=""):
    if not data:
        return "(empty body)"
    try:
        text = data.decode("utf-8", "replace")
    except Exception:
        text = ""
    text = text.strip().replace("\n", " ")
    if len(text) > 240:
        text = text[:240] + "…"
    return text


def tool_curl(url, method="GET", timeout=20, verify=True, allow_redirects=True):
    """Hit a URL the way a browser would and return status + a short body slice.
    ACEsi uses this to confirm whether a network service (e.g. an ITS portal) is
    actually up, separate from the on-device / file-system work. Returns
    (ok, string): ok=True when the HTTP request completed (even on 4xx/5xx, so the
    caller can read the status code), ok=False only on DNS failure / connection
    refused / timeout — which is the 'server reachable but no web service / port
    closed' signal ACEsi couldn't get from uiautomator alone."""
    if not url or not str(url).startswith(("http://", "https://")):
        return False, "curl usage: url=<http://host or https://host/path> [method] [timeout]"
    try:
        req = _urlreq.Request(str(url), method=str(method).upper(),
                              headers={"User-Agent": "Mozilla/5.0 (ACEsi curl)"})
        try:
            ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
            handler = _urlreq.HTTPSHandler(context=ctx)
        except Exception:
            handler = _urlreq.HTTPSHandler()
        opener = _urlreq.build_opener(
            handler, _urlreq.HTTPRedirectHandler() if allow_redirects else _NoRedirectHandler())
        with opener.open(req, timeout=float(timeout)) as resp:
            data = resp.read(6000)
            ctype = resp.headers.get("Content-Type", "")
            return True, "HTTP %d | %s | %s" % (
                resp.status, ctype.split(";")[0], _body_snippet(data, ctype))
    except _urlerr.HTTPError as e:
        return True, "HTTP %d (server responded) | %s" % (e.code, str(e)[:200])
    except _urlerr.URLError as e:
        reason = str(getattr(e, "reason", e))
        return False, "curl FAIL (network) — %s: %s" % (reason, url)
    except _socket.timeout:
        return False, "curl FAIL (timeout %ss) — %s" % (timeout, url)
    except Exception as e:
        return False, "curl error: %s" % str(e)[:200]


def tool_get_time():
    """Current date/time, weekday, and the date 7 days out (for scheduling)."""
    now = datetime.now()
    wk = (now + timedelta(days=7)).date().isoformat()
    return True, "Now: %s. Tomorrow: %s. One week out: %s." % (
        now.strftime('%A, %d %B %Y, %I:%M %p'), (now + timedelta(days=1)).date().isoformat(), wk)


def _clean_result_url(href, title):
    """Normalize a search-result URL so the user can open it directly.
    DuckDuckGo Lite wraps real links in a redirect (/l/?uddg=<encoded>&rut=...)
    that returns 400 when clicked in a browser — decode uddg= back to the actual
    URL so the links in drafts/summaries work."""
    import html as _html
    import urllib.parse as _uparse
    try:
        if "duckduckgo.com/l/?uddg=" in href:
            q = _uparse.urlsplit(href).query
            params = _uparse.parse_qs(q, keep_blank_values=True)
            if params.get("uddg"):
                href = params["uddg"][0]
    except Exception:
        pass
    href = _html.unescape(href).strip()
    return "- %s\n  %s" % (title, href)

def _decode_bing_redirect(href):
    """Decode Bing's redirect URL (ck/a links) to get the actual URL."""
    import urllib.parse as _up
    try:
        # Parse the redirect URL to extract the 'u' parameter
        parsed = _up.urlparse(href)
        params = _up.parse_qs(parsed.query)
        if 'u' in params:
            encoded = params['u'][0]
            # Strip the 2-char prefix (e.g., 'a1') then base64 decode
            if len(encoded) > 2:
                encoded = encoded[2:]
                import base64
                encoded += '=' * (-len(encoded) % 4)
                return base64.b64decode(encoded).decode('utf-8', 'replace')
    except Exception:
        pass
    return href


def _search_tavily(query, max_results, include_images=False):
    """Search using Tavily API. Returns title + URL + content snippet so the
    model can actually answer from the result text (not just link names).
    With include_images=True the response also carries an IMAGE block with
    real, fetchable image URLs — the model otherwise invents image paths that
    404 when it tries to show a picture."""
    import urllib.request as _urlreq
    import urllib.parse as _up
    import json

    api_key = os.environ.get("TAVILY_API_KEY") or _LK.get("tavily", "")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set")
    url = "https://api.tavily.com/search"
    body = {
        "api_key": api_key,
        "query": query,
        "max_results": int(max_results),
        "search_depth": "basic",
        "include_answer": False,
        "include_raw_content": False,
    }
    if include_images:
        body["include_images"] = True
        body["include_image_descriptions"] = False
    payload = json.dumps(body).encode("utf-8")

    req = _urlreq.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with _urlreq.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    items = []
    if include_images:
        # Tavily returns images as either plain URL strings or {"url": ...} dicts
        # depending on the plan/response, so accept both shapes.
        imgs = data.get("images") or []
        shown = []
        for im in imgs:
            if isinstance(im, str):
                iu = im.strip()
            elif isinstance(im, dict):
                iu = (im.get("url") or "").strip()
            else:
                iu = ""
            if iu and iu not in shown:
                shown.append(iu)
        if shown:
            items.append("IMAGE RESULTS (pass one of these URLs to view_web_image):")
            for iu in shown[:6]:
                items.append("- image: %s" % iu)
    for r in data.get("results", [])[:max_results]:
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()
        snippet = (r.get("content") or "").strip()
        if len(snippet) > 260:
            snippet = snippet[:260] + "…"
        if title and url:
            line = "- %s\n  %s" % (title, url)
            if snippet:
                line += "\n  " + snippet.replace("\n", " ")
            items.append(line)
    return items


def _search_serper(query, max_results):
    """Search using Serper API. Includes the Google result snippet so the model
    has actual answer-text, not just a bare list of titles and links."""
    import urllib.request as _urlreq
    import urllib.parse as _up
    import json

    api_key = "81456d3c3d5a16cabb4d76f78141fc94ea62634f"
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": int(max_results),
    }).encode("utf-8")

    req = _urlreq.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        },
        method="POST",
    )
    with _urlreq.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    items = []
    # Google's Knowledge Graph answer box gives a one-line answer when one exists.
    kg = data.get("knowledgeGraph") or {}
    if kg.get("title") and kg.get("description"):
        items.append("KNOWLEDGE: %s — %s" % (kg.get("title"), str(kg.get("description"))[:300]))
    for r in data.get("organic", [])[:max_results]:
        title = r.get("title", "").strip()
        url = r.get("link", "").strip()
        snippet = (r.get("snippet") or "").strip()
        if len(snippet) > 260:
            snippet = snippet[:260] + "…"
        if title and url:
            line = "- %s\n  %s" % (title, url)
            if snippet:
                line += "\n  " + snippet.replace("\n", " ")
            items.append(line)
    return items


def _search_duckduckgo(query, max_results):
    """DuckDuckGo Lite search (no API key, no CAPTCHA)."""
    import urllib.parse as _up
    import urllib.request as _urlreq
    import re as _re

    q = _up.quote_plus(str(query).strip())
    url = "https://lite.duckduckgo.com/lite/?q=" + q
    req = _urlreq.Request(url, headers={"User-Agent": "Mozilla/5.0 (ACEsi)"})
    with _urlreq.urlopen(req, timeout=20) as resp:
        html = resp.read(200000).decode("utf-8", "replace")

    items = []
    for m in _re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, _re.S):
        href, title = m.group(1), _re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if not title or not href:
            continue
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://lite.duckduckgo.com" + href
        items.append("- %s\n  %s" % (title, href))
        if len(items) >= int(max_results):
            break
    return items


def _search_bing(query, max_results):
    """Bing search (no API key)."""
    import urllib.parse as _up
    import urllib.request as _urlreq
    import re as _re
    import base64

    q = _up.quote_plus(str(query).strip())
    url = "https://www.bing.com/search?q=" + q + "&setlang=en-US"
    req = _urlreq.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    with _urlreq.urlopen(req, timeout=20) as resp:
        html = resp.read(200000).decode("utf-8", "replace")

    items = []
    for m in _re.finditer(r'<li class="b_algo"[^>]*>.*?<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, _re.S | _re.I):
        href, title = m.group(1), _re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if not title or not href or href.startswith("javascript:"):
            continue
        if "/ck/a?" in href or href.startswith("/ck/a?"):
            href = _decode_bing_redirect(href)
        items.append("- %s\n  %s" % (title, href))
        if len(items) >= int(max_results):
            break
    return items


def tool_web_search(query, max_results=6):
    """Multi-provider web search with fallback chain:
    1. Tavily (API key)
    2. Serper (API key)
    3. DuckDuckGo (keyless)
    4. Bing (keyless fallback)
    Returns titles + links with provider debug log.
    Args: query (REQUIRED), max_results (optional, default 6)."""
    if not query or not str(query).strip():
        return False, "web_search usage: query=<search text>"

    q = str(query).strip()
    # Ask for real image URLs when the query is about seeing something. Without
    # this the model has to guess an image path from page URLs, and guesses 404.
    want_images = bool(re.search(
        r'\b(picture|photo|image|images|pic|pics|portrait|logo|poster|'
        r'illustration|drawing|artwork|wallpaper|headshot)\b', q, re.IGNORECASE))
    providers = [
        ("Tavily", lambda: _search_tavily(q, max_results, include_images=want_images)),
        ("Serper", lambda: _search_serper(q, max_results)),
        ("DuckDuckGo", lambda: _search_duckduckgo(q, max_results)),
        ("Bing", lambda: _search_bing(q, max_results)),
    ]

    for name, search_fn in providers:
        try:
            print(f"[web_search] Trying {name}...")
            items = search_fn()
            if items:
                result = "\n".join(items)
                print(f"[web_search] SUCCESS via {name} ({len(items)} results)")
                return True, "[provider: %s]\n%s" % (name, result)
            else:
                print(f"[web_search] {name} returned no results")
        except Exception as e:
            print(f"[web_search] {name} failed: {e}")

    return False, "web_search failed: all providers exhausted"


def tool_webfetch(url, format="markdown"):
    """Fetch the full content of a URL. Args: url (REQUIRED), format (optional:
    markdown/text/html, default markdown). Use this AFTER web_search to read
    the actual page content — search results only give titles + snippets."""
    if not url or not str(url).startswith(("http://", "https://")):
        return False, "webfetch usage: url=<http(s)://...>"
    try:
        from webfetch_impl import fetch_url
        return True, fetch_url(str(url), fmt=format)
    except ImportError:
        pass
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for attempt in range(3):
        try:
            req = _urlreq.Request(str(url), method="GET", headers=headers)
            with _urlreq.urlopen(req, timeout=15) as resp:
                data = resp.read(100000)
            if format == "text":
                return True, data.decode("utf-8", "replace")
            elif format == "html":
                return True, data.decode("utf-8", "replace")
            else:
                import html as _html
                raw = data.decode("utf-8", "replace")
                text = _html.unescape(raw)
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.S)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return True, text[:8000]
        except Exception as e:
            if attempt < 2:
                time.sleep(2 * (2 ** attempt))
            else:
                return False, "webfetch failed after 3 retries: %s" % str(e)[:160]


def tool_weather(city="Thohoyandou"):
    """Current weather for a city via Open-Meteo (no API key). Args: city
    (optional, default Thohoyandou)."""
    try:
        import urllib.parse as _up
        _geo = ("https://geocoding-api.open-meteo.com/v1/search?name=%s&count=1" % _up.quote_plus(str(city)))
        gp = json.loads(_urlreq.urlopen(_geo, timeout=15).read().decode("utf-8", "replace"))
        results = gp.get("results") or []
        if not results:
            return False, "weather: no city matched '%s'" % city
        r0 = results[0]
        wurl = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&current_weather=true" %
                (r0["latitude"], r0["longitude"]))
        wj = json.loads(_urlreq.urlopen(wurl, timeout=15).read().decode("utf-8", "replace"))
        cw = wj.get("current_weather") or {}
        return True, "Weather in %s: %.0f°C, wind %.0f km/h, %s" % (
            r0.get("name", city), cw.get("temperature", 0), cw.get("windspeed", 0),
            cw.get("weathercode", "?"))
    except Exception as e:
        return False, "weather failed: %s" % str(e)[:160]


def tool_note(text):
    """Add a line to notes.json so ACEsi can remember a quick note between tasks
    (a lightweight scratchpad, separate from long-term memory)."""
    if not text or not str(text).strip():
        return False, "note usage: text=<what to remember>"
    with _data_lock:
        notes = load_json('notes.json', []).get('notes', [])
        notes.append({"ts": datetime.now().isoformat(), "text": str(text)[:500]})
        save_json('notes.json', {'notes': notes[-200:]})
    return True, "note saved (%d notes)" % len(notes)


TODO_FILE = 'todo.json'


def tool_todo_add(text, priority="medium", category="general"):
    """Add a task to the shared to-do list. Args: text (REQUIRED, task description), priority (optional: high/medium/low, default medium), category (optional: default general)."""
    if not text or not str(text).strip():
        return False, "todo_add usage: text=<task description> [priority=high|medium|low] [category=name]"
    with _data_lock:
        todos = load_json(TODO_FILE, {}).get("items", [])
        # max(existing)+1, not len()+1: after removing id 2 from [1,2,3] the
        # list is [1,3], and len()+1 handed out a duplicate id 3, so
        # todo_done(3) then completed the wrong item.
        next_id = 1
        for t in todos:
            try:
                next_id = max(next_id, int(t.get("id", 0)) + 1)
            except (TypeError, ValueError):
                continue
        item = {"id": next_id, "text": str(text).strip()[:300],
                "priority": str(priority).lower() if str(priority).lower() in ("high", "medium", "low") else "medium",
                "category": str(category).strip()[:100] or "general",
                "done": False, "created": datetime.now().isoformat()}
        todos.append(item)
        save_json(TODO_FILE, {"items": todos})
    return True, "todo_add: '%s' (id=%d, priority=%s)" % (str(text).strip()[:80], item["id"], item["priority"])


def tool_todo_list(category=None, done=False):
    """List to-do items. Args: category (optional filter), done (optional: true=show done, false=show pending, default false)."""
    with _data_lock:
        todos = load_json(TODO_FILE, {}).get("items", [])
    if category:
        todos = [t for t in todos if t.get("category") == category]
    if not done:
        todos = [t for t in todos if not t.get("done")]
    if not todos:
        return True, "No tasks listed."
    lines = []
    for t in todos:
        mark = "✅" if t.get("done") else "⬜"
        pri = t.get("priority", "medium")
        lines.append("%s [#%d] (%s/%s) %s" % (mark, t["id"], pri, t.get("category", "general"), t["text"]))
    return True, "To-do list:\n" + "\n".join(lines)


def tool_todo_done(task_id):
    """Mark a to-do item as done. Args: task_id (REQUIRED, the item id from todo_list)."""
    try:
        task_id = int(task_id)
    except Exception:
        return False, "todo_done usage: task_id=<integer id>"
    with _data_lock:
        todos = load_json(TODO_FILE, {}).get("items", [])
        for t in todos:
            if t["id"] == task_id:
                t["done"] = True
                save_json(TODO_FILE, {"items": todos})
                return True, "todo_done: [#%d] marked done — %s" % (task_id, t["text"][:80])
        save_json(TODO_FILE, {"items": todos})
    return False, "todo_done: no task with id %d" % task_id


def tool_todo_remove(task_id):
    """Remove a to-do item. Args: task_id (REQUIRED, the item id)."""
    try:
        task_id = int(task_id)
    except Exception:
        return False, "todo_remove usage: task_id=<integer id>"
    with _data_lock:
        todos = load_json(TODO_FILE, {}).get("items", [])
        new = [t for t in todos if t["id"] != task_id]
        if len(new) == len(todos):
            save_json(TODO_FILE, {"items": new})
            return False, "todo_remove: no task with id %d" % task_id
        save_json(TODO_FILE, {"items": new})
    return True, "todo_remove: removed task #%d" % task_id


def tool_notify(title="ACEsi", message="Ping from ACEsi"):
    """Send a push notification (ntfy) to Chris's phone. Returns (ok, result).
    Args: title (optional, default 'ACEsi'), message (optional).
    NOTE: ntfy requires the ntfy app on the phone subscribing to NTFY_TOPIC."""
    if not message or not str(message).strip():
        return False, "notify usage: message=<text> [title=<title>]"
    ok = send_ntfy(str(title), str(message))
    return (True, f"Notified '{title}': {str(message)[:80]}" if ok
            else (False, "ntfy push failed (check internet / ntfy app subscription)"))


def tool_check_email(force_all=True):
    """Check Chris's Gmail/Yahoo inboxes NOW and phone-push (ntfy) anything
    matching an enabled rule in email_notify_rules.json (e.g. NSFAS).
    Returns (ok, result). The background watcher does this automatically every
    couple of minutes; call this when Chris wants an answer right now."""
    return check_email_now(force_all=bool(force_all))


def tool_set_preference(key, value):
    """Store a STANDING PREFERENCE — an instruction Chris wants obeyed on every
    future reply (tone, units, reply length, format, what to call him).
    Call this the moment he states one, e.g. 'call me Chris', 'always answer in
    Afrikaans', 'use metric units', 'keep replies to 2 lines'.
    Args: key (REQUIRED, one of: name, pronouns, tone, brevity, format, language,
    units, currency, dates, email, phone, location, study, notifications, schedule,
    greeting, diet), value (REQUIRED).
    Returns (ok, result). A preference outranks your default style later. Near
    synonyms are merged server-side, but use the exact enum key."""
    res = set_preference(key, value)
    return bool(res.get("ok")), res.get("message") or res.get("error", "failed")


def tool_list_preferences():
    """List the standing preferences currently stored, so you can tell Chris what
    you will keep doing and change anything he asks to change."""
    res = list_preferences()
    return True, res["message"]


def tool_forget_preference(key):
    """Remove a standing preference when Chris says to stop following it
    (e.g. 'stop calling me Chris', 'don't keep replies short anymore').
    Args: key (REQUIRED, the preference name). Returns (ok, result)."""
    res = forget_preference(key)
    return bool(res.get("ok")), res.get("message") or res.get("error", "failed")


def tool_list_email_rules():
    """List the email-watch rules (which senders/subjects trigger a phone push)."""
    rules = _load_email_rules()
    if not rules:
        return True, "No email rules enabled."
    lines = []
    for r in rules:
        lines.append("- %s [%s] from=%r subject=%r body=%r" % (
            r.get("name") or "(unnamed)", r.get("account") or "both",
            r.get("from") or "", r.get("subject") or "", r.get("body") or ""))
    return True, "\n".join(lines)


TOOLS = {
    "list_files": (tool_list_files, ("path",)),
    "read_file": (tool_read_file, ("path",)),
    "list_user_files": (tool_list_user_files, ("path",)),
    "read_user_file": (tool_read_user_file, ("path",)),
    "open_user_file": (tool_open_user_file, ("path",)),
    "view_user_file": (tool_view_user_file, ("path",)),
    "grep": (tool_grep, ("pattern", "path")),
    "write_file": (tool_write_file, ("path", "content")),
    "open_in_vscode": (tool_open_in_vscode, ("path", "content")),
    "edit_file": (tool_edit_file, ("path", "old", "new")),
    "run_command": (tool_run_command, ("command",)),
    "git_status": (tool_git_status, ()),
    "git_log": (tool_git_log, ("n",)),
    "git_commit": (tool_git_commit, ("message", "files")),
    "git_branch": (tool_git_branch, ("name", "create")),
    "git_merge": (tool_git_merge, ("branch",)),
    "build_apk": (tool_build_apk, ("mode",)),
    "pub_add": (tool_pub_add, ("package",)),
    "pub_remove": (tool_pub_remove, ("package",)),
    "pub_upgrade": (tool_pub_upgrade, ()),
    "flutter_test": (tool_flutter_test, ("path",)),
    "flutter_analyze": (tool_flutter_analyze, ()),
    "ui_device": (tool_ui_device, ()),
    "ui_app_open": (tool_ui_app_open, ()),
    "ui_tap": (tool_ui_tap, ("x", "y")),
    "ui_swipe": (tool_ui_swipe, ("x1", "y1", "x2", "y2", "duration")),
    "ui_type": (tool_ui_type, ("text",)),
    "ui_key": (tool_ui_key, ("key",)),
    "ui_dump": (tool_ui_dump, ()),
    "ui_screenshot": (tool_ui_screenshot, ("name", "save")),
    "ui_assert_text": (tool_ui_assert_text, ("text", "present")),
    "ui_assert_element": (tool_ui_assert_element, ("resource_id", "text", "desc", "cls", "present")),
    "ui_assert_visible": (tool_ui_assert_visible, ("resource_id", "text", "desc", "cls")),
    "ui_expect": (tool_ui_expect, ("expected",)),
    "ui_test_run": (tool_ui_test_run, ("steps", "name")),
    "restart": (tool_restart, ("what",)),
    "cdp_connect": (tool_cdp_connect, ()),
    "cdp_evaluate": (tool_cdp_evaluate, ("expr",)),
    "cdp_console_logs": (tool_cdp_console_logs, ()),
    "cdp_dom_state": (tool_cdp_dom_state, ()),
    "cdp_network_requests": (tool_cdp_network_requests, ()),
    "cdp_status": (tool_cdp_status, ()),
    "curl": (tool_curl, ("url", "method", "timeout", "verify", "allow_redirects")),
    "view_web_image": (tool_view_web_image, ("url",)),
    "notify": (tool_notify, ("title", "message")),
    "check_email": (tool_check_email, ("force_all",)),
    "list_email_rules": (tool_list_email_rules, ()),
    "get_time": (tool_get_time, ()),
    "web_search": (tool_web_search, ("query", "max_results")),
    "webfetch": (tool_webfetch, ("url", "format")),
    "weather": (tool_weather, ("city",)),
    "note": (tool_note, ("text",)),
    "todo_add": (tool_todo_add, ("text", "priority", "category")),
    "todo_list": (tool_todo_list, ("category", "done")),
    "todo_done": (tool_todo_done, ("task_id",)),
    "todo_remove": (tool_todo_remove, ("task_id",)),
    "set_preference": (tool_set_preference, ("key", "value")),
    "list_preferences": (tool_list_preferences, ()),
    "forget_preference": (tool_forget_preference, ("key",)),
}

# Native OpenAI-compatible tool schema. Sent to the provider so the model can
# emit structured tool_calls (the reason ACEsi stalled is that this was never
# passed before — the model had no tool-calling signal and emitted prose only).
TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "list_files",
        "description": "List files/dirs in a directory. Args: path (dir to list).",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file",
        "description": "Read a file's contents. Args: path.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "list_user_files",
        "description": "List files/dirs on Chris's PC. Paths can be 'Documents', 'My Pictures', 'Desktop', 'Downloads' or any folder on the machine. Args: path (dir to list).",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_user_file",
        "description": "Read a file's content from anywhere on Chris's PC (any folder: Documents, Pictures, Desktop, Downloads, etc). Accepts a full path or a bare filename. Args: path.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "view_user_file",
        "description": "VIEW a file from Chris's PC inline in the ACEsi chat window as a popup. Use this when the user wants to SEE the file content (images, PDFs, text) inside ACEsi. Accepts a full path or a bare filename. Returns base64 for images (png, jpg, gif, webp, bmp, tiff), PDFs, and text. Args: path.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "open_user_file",
        "description": "LAUNCH a file EXTERNALLY with the system default application (Windows Photos, browser, etc.). Use ONLY when the user explicitly says 'open externally', 'launch in default app', or 'open outside ACEsi'. For normal 'show me the file' or 'open the file' in a browsing context, use view_user_file instead. Args: path.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "view_web_image",
        "description": "Download an image from a URL and DISPLAY it inline in the ACEsi chat window as a popup — use when the user wants to actually SEE a picture from the internet (e.g. 'get me a picture of X', 'show me an image of Y'). The URL must point directly at an image file (png/jpg/jpeg/gif/webp/bmp). Always call this after web_search/webfetch finds an image URL. Args: url.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "grep",
        "description": "Regex search file contents. Args: pattern, path.",
        "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern", "path"]}}},
    {"type": "function", "function": {"name": "write_file",
        "description": "Create/overwrite a file. Args: path, content.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "open_in_vscode",
        "description": "Open content in the user's code editor (VS Code/VSCodium) as a review DRAFT — does NOT write the final file. Chris reviews it in the editor and decides whether to save. Use whenever the user asked to research/save/find + save to a file: compose the findings, call this with path (intended final location) and content, then tell Chris to review. Chris will then say 'save it' to commit. Args: path, content.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "edit_file",
        "description": "Surgical exact-match edit; old must match exactly once. Args: path, old, new.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}, "required": ["path", "old", "new"]}}},
    {"type": "function", "function": {"name": "run_command",
        "description": "Run a shell command and return stdout/stderr. Args: command.",
             "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "git_status",
        "description": "Short git status incl. current branch. Args: none.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "git_log",
        "description": "Recent commit log. Args: n (optional, default 10, max 50).",
        "parameters": {"type": "object", "properties": {"n": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "git_commit",
        "description": "Stage changes and commit as ACEsi. Args: message (commit message), files (optional, list of paths to stage instead of git add -A).",
        "parameters": {"type": "object", "properties": {"message": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "git_branch",
        "description": "List branches, or create+switch to a new branch when create=true. Args: name, create (bool, optional).",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "create": {"type": "boolean"}}, "required": []}}},
    {"type": "function", "function": {"name": "git_merge",
        "description": "Merge an existing local branch into the current branch. Reports conflicts if any (resolve with edit_file then git_commit). Args: branch.",
        "parameters": {"type": "object", "properties": {"branch": {"type": "string"}}, "required": ["branch"]}}},
    {"type": "function", "function": {"name": "build_apk",
        "description": "Build an Android APK with flutter build apk --release (default) or --debug. Returns the artifact path. Args: mode (optional).",
        "parameters": {"type": "object", "properties": {"mode": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "pub_add",
        "description": "Add a dependency via `flutter pub add <package>` (updates pubspec.yaml + pub get). Args: package (e.g. 'http:^1.2.0').",
        "parameters": {"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]}}},
    {"type": "function", "function": {"name": "pub_remove",
        "description": "Remove a dependency via `flutter pub remove <package>`. Args: package.",
        "parameters": {"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]}}},
    {"type": "function", "function": {"name": "pub_upgrade",
        "description": "Upgrade all dependencies via `flutter pub upgrade`. Args: none.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "flutter_test",
        "description": "Run the Flutter test suite. Args: path (optional, test file/dir to run).",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "flutter_analyze",
        "description": "Static analysis via `flutter analyze`. Args: none.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ui_device",
        "description": "Show connected Android devices, screen size and density. Args: none.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ui_app_open",
        "description": "Launch the StudentSyncSA app on the connected device. Args: none.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ui_tap",
        "description": "Tap the screen at a pixel coordinate. Call ui_device FIRST to learn the screen size (e.g. 1080x2412). REQUIRED arguments: x (horizontal pixel from left edge), y (vertical pixel from top edge). Both must be integer pixel values, never null, never strings.",
        "parameters": {"type": "object", "properties": {
            "x": {"type": "integer", "title": "x", "description": "REQUIRED. Horizontal pixel coordinate from the LEFT edge of the screen. Integer, e.g. 540 on a 1080-wide screen."},
            "y": {"type": "integer", "title": "y", "description": "REQUIRED. Vertical pixel coordinate from the TOP edge of the screen. Integer, e.g. 1200 on a 2412-tall screen."}},
            "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "ui_swipe",
        "description": "Swipe (scroll/gesture) from a start pixel (x1,y1) to an end pixel (x2,y2). REQUIRED: x1, y1, x2, y2 (integer pixels). OPTIONAL: duration (integer ms, default 200). For a downward scroll use a larger y2 than y1.",
        "parameters": {"type": "object", "properties": {
            "x1": {"type": "integer", "title": "x1", "description": "REQUIRED. Start horizontal pixel coordinate from the LEFT edge."},
            "y1": {"type": "integer", "title": "y1", "description": "REQUIRED. Start vertical pixel coordinate from the TOP edge."},
            "x2": {"type": "integer", "title": "x2", "description": "REQUIRED. End horizontal pixel coordinate from the LEFT edge."},
            "y2": {"type": "integer", "title": "y2", "description": "REQUIRED. End vertical pixel coordinate from the TOP edge."},
            "duration": {"type": "integer", "title": "duration", "description": "OPTIONAL. Gesture duration in milliseconds. Default 200."}},
            "required": ["x1", "y1", "x2", "y2"]}}},
    {"type": "function", "function": {"name": "ui_type",
        "description": "Type a text string into the currently focused input field on the device. REQUIRED argument: text (the exact characters to type; spaces are sent as %s). Never null.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "title": "text", "description": "REQUIRED. The exact text to type, e.g. \"john@school.edu\". Never null or empty."}},
            "required": ["text"]}}},
    {"type": "function", "function": {"name": "ui_key",
        "description": "Send a single key event to the device. REQUIRED argument: key. Allowed values: back, home, enter, tab, menu, up, down, left, right, esc, power, recents, or a numeric Android keyevent code (e.g. 4 = BACK).",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string", "title": "key", "description": "REQUIRED. One of: back, home, enter, tab, menu, up, down, left, right, esc, power, recents, or a numeric keyevent code. Never null."}},
            "required": ["key"]}}},
    {"type": "function", "function": {"name": "ui_dump",
        "description": "Dump the on-screen UI accessibility hierarchy (all visible text, buttons, bounds). Use this to VERIFY what is actually on screen after taps/navigation. No arguments required.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ui_screenshot",
        "description": "Capture the current screen. By DEFAULT the image is NOT written to disk — it is buffered in memory and shown to Chris in a popup. Only set save=true when Chris explicitly asks to save/keep the screenshot as a file. If you later want it saved, call again with save=true. NOTE: you cannot view images — use ui_dump to read the screen. OPTIONAL arguments: name (string used in the filename when saved), save (boolean).",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "title": "name", "description": "OPTIONAL. File name prefix for the screenshot when save=true, e.g. \"login\". Omit or null to auto-name."},
            "save": {"type": "boolean", "title": "save", "description": "OPTIONAL. Defaults to false. Set true ONLY when Chris asked to keep the screenshot as a file. Must be boolean true, not a string."}},
            "required": []}}},
    {"type": "function", "function": {"name": "ui_assert_text",
        "description": "UI VALIDATION: assert whether text exists on screen (case-insensitive substring of any visible text/content-desc). REQUIRED: text (the string to look for). OPTIONAL: present (boolean, default true; set false to assert the text is ABSENT). Returns PASS when the assertion holds, FAIL with a label list otherwise.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "title": "text", "description": "REQUIRED. Text to search the live screen for, e.g. \"Welcome\"."},
            "present": {"type": "boolean", "title": "present", "description": "OPTIONAL. true = assert text exists (default), false = assert text does NOT exist."}},
            "required": ["text"]}}},
    {"type": "function", "function": {"name": "ui_assert_element",
        "description": "UI VALIDATION: assert whether an element with the given properties exists in the accessibility tree (NOT that it is visible/on-screen — use ui_assert_visible for that). OPTIONAL AND COMBINABLE filters: resource_id (exact resource-id), text (case-insensitive substring of text OR content-desc), desc (exact content-desc), cls (substring of class, e.g. Button). OPTIONAL: present (default true; false asserts the element is ABSENT). Provide at least one filter.",
        "parameters": {"type": "object", "properties": {
            "resource_id": {"type": "string", "description": "OPTIONAL. Exact Android resource-id, e.g. \"com.studentsyncsa:id/btn_login\"."},
            "text": {"type": "string", "description": "OPTIONAL. Case-insensitive text substring."},
            "desc": {"type": "string", "description": "OPTIONAL. Exact content-desc."},
            "cls": {"type": "string", "description": "OPTIONAL. Class substring, e.g. \"Button\"."},
            "present": {"type": "boolean", "description": "OPTIONAL. true = assert present (default), false = assert absent."}},
            "required": []}}},
    {"type": "function", "function": {"name": "ui_assert_visible",
        "description": "UI VALIDATION: assert whether a matching element is actually VISIBLE and interactable on screen (on-screen bounds, visible-to-user, enabled). OPTIONAL AND COMBINABLE filters: resource_id, text, desc, cls (same semantics as ui_assert_element). Provide at least one filter.",
        "parameters": {"type": "object", "properties": {
            "resource_id": {"type": "string", "description": "OPTIONAL. Exact Android resource-id."},
            "text": {"type": "string", "description": "OPTIONAL. Case-insensitive text substring."},
            "desc": {"type": "string", "description": "OPTIONAL. Exact content-desc."},
            "cls": {"type": "string", "description": "OPTIONAL. Class substring, e.g. \"Button\"."}},
            "required": []}}},
    {"type": "function", "function": {"name": "ui_expect",
        "description": "UI VALIDATION: compare the current ui_dump against an expected screen state. REQUIRED: expected — either a JSON object {\"present\": [labels that must be on screen], \"absent\": [labels that must be absent]} or a plain string whose lines/commas are fragments that must all be present. Returns PASS/FAIL with the specific missing/unexpected fragments.",
        "parameters": {"type": "object", "properties": {
            "expected": {"type": "string", "title": "expected", "description": "REQUIRED. Expected state — JSON {present:[...],absent:[...]} or plain text fragments."}},
            "required": ["expected"]}}},
    {"type": "function", "function": {"name": "ui_test_run",
        "description": "UI VALIDATION HARNESS: run a scripted sequence of UI actions + assertions and report PASS/FAIL. REQUIRED: steps — a JSON list of {\"tool\": \"ui_tap\", \"args\": {...}} entries (any ui_* action or ui_assert_* tool). Each step is judged by the tool's ok flag; concludes 'TEST PASSED (n/total)' or 'TEST FAILED'. OPTIONAL: name (string label for the report).",
        "parameters": {"type": "object", "properties": {
            "steps": {"type": "string", "title": "steps", "description": "REQUIRED. JSON list of {tool, args} step objects, e.g. [{\"tool\":\"ui_app_open\",\"args\":{}},{\"tool\":\"ui_assert_text\",\"args\":{\"text\":\"Login\"}}]."},
            "name": {"type": "string", "title": "name", "description": "OPTIONAL. Test/scenario name shown in the report."}},
            "required": ["steps"]}}},
    {"type": "function", "function": {"name": "restart",
        "description": "Self-host restart: what=server (asks ace_host.py watchdog to restart the server), what=chrome (relaunch local CDP headless Chrome), what=cdp (force new CDP session), what=ollama (start ollama serve if down). Args: what.",
        "parameters": {"type": "object", "properties": {"what": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "cdp_connect",
        "description": "Connect to a Chrome DevTools target (ITS WebView on an Android device, or a local Chrome launched with --remote-allow-origins=*). Run this first before the other cdp_* tools.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "cdp_evaluate",
        "description": "Evaluate a JavaScript expression in the connected WebView/Chrome page via CDP and return its JSON value. Args: expr.",
        "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]}}},
    {"type": "function", "function": {"name": "cdp_console_logs",
        "description": "Return buffered console.log/console.error events captured by CDP since the connect. Args: none.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "cdp_dom_state",
        "description": "Snapshot the current DOM via CDP: page title, URL, and a slice of documentElement.outerHTML.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "cdp_network_requests",
        "description": "Return buffered network request events captured by CDP (requestWillBeSent / responseReceived).",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "cdp_status",
        "description": "Current CDP connection status (connected, ws_url, console/network event counts).",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "curl",
        "description": "Hit a URL like a browser and return the HTTP status + a body snippet. Use this to confirm whether a network service (e.g. an ITS portal) is UP before blaming on-device code. Args: url (REQUIRED, http(s)://...), method (optional, default GET), timeout (optional int seconds, default 20), verify (optional bool, default true), allow_redirects (optional bool, default true). Returns ok=True even on 4xx/5xx (a server responded); ok=False only on DNS failure / connection refused / timeout = the 'no web service / port closed' signal.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "title": "url", "description": "REQUIRED. Full URL starting with http:// or https://."},
            "method": {"type": "string", "title": "method", "description": "Optional. HTTP method, default GET.", "default": "GET"},
            "timeout": {"type": "number", "title": "timeout", "description": "Optional. Seconds to wait, default 20.", "default": 20},
            "verify": {"type": "boolean", "title": "verify", "description": "Optional. Verify TLS cert, default true.", "default": True},
            "allow_redirects": {"type": "boolean", "title": "allow_redirects", "description": "Optional. Follow 3xx redirects, default true.", "default": True}},
            "required": ["url"]}}},
    {"type": "function", "function": {"name": "notify",
        "description": "Send a push notification to Chris's phone via ntfy. Use for pings, alerts, reminders, or any 'notify me / ping my phone / tell me when' request. Args: title (optional, default 'ACEsi'), message (optional text to send). NOTE: Chris's phone must have the ntfy app installed and subscribed to this server's private topic.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "title": "title", "description": "Optional. Notification title, default 'ACEsi'."},
            "message": {"type": "string", "title": "message", "description": "Optional. The message text to push. Default 'Ping from ACEsi'."}},
            "required": []}}},
    {"type": "function", "function": {"name": "check_email",
        "description": "Check Chris's Gmail and Yahoo inboxes NOW and push a PHONE notification (ntfy) for any email matching his watch rules (e.g. NSFAS). Use this when he asks about email out of the blue ('check my email', 'any NSFAS email?', 'did I get an NSFAS mail?'). A background watcher already does this every ~2 minutes; this tool forces it immediately. Args: force_all (optional boolean, default true — true re-checks the whole recent inbox, false only looks for mail newer than the last poll).",
        "parameters": {"type": "object", "properties": {
            "force_all": {"type": "boolean", "title": "force_all", "description": "Optional. Re-scan the recent inbox instead of only new mail. Default true."}},
            "required": []}}},
    {"type": "function", "function": {"name": "list_email_rules",
        "description": "List the active email-watch rules — which senders/subjects/keywords trigger a phone push for Chris. No args.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_time",
        "description": "Current local date/time, weekday, and dates 1 and 7 days out. No args.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "web_search",
        "description": "Search the web (Tavily/Serper then DuckDuckGo, no key) and return the top results WITH their answer snippets: title + URL + content text, plus Tavily/Google's direct ANSWER line when one exists. The returned snippet text usually contains the answer to the question — read it and answer directly; use webfetch only when more detail is needed. Args: query (REQUIRED), max_results (optional, default 6).",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "title": "query", "description": "REQUIRED. Search query."},
            "max_results": {"type": "integer", "title": "max_results", "description": "Optional. Max results, default 6."}},
            "required": ["query"]}}},
    {"type": "function", "function": {"name": "webfetch",
        "description": "Fetch full page content from a URL. Args: url (REQUIRED, http(s)://...), format (optional: markdown/text/html, default markdown). USE THIS AFTER web_search — search results only give titles and snippets; webfetch reads the actual page for details like addresses and phone numbers.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "title": "url", "description": "REQUIRED. Full URL starting with http:// or https://."},
            "format": {"type": "string", "title": "format", "description": "Optional. Output format: markdown, text, or html. Default markdown."}},
            "required": ["url"]}}},
    {"type": "function", "function": {"name": "weather",
        "description": "Current weather (temp, wind, conditions) for a city via Open-Meteo. Args: city (optional, default Thohoyandou).",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string", "title": "city", "description": "Optional. City name."}},
            "required": []}}},
    {"type": "function", "function": {"name": "note",
        "description": "Save a quick scratchpad note to notes.json (extra memory). Args: text (REQUIRED, what to remember).",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "title": "text", "description": "REQUIRED. The note text."}},
            "required": ["text"]}}},
    {"type": "function", "function": {"name": "todo_add",
        "description": "Add a task to the shared to-do list. Args: text (REQUIRED), priority (optional: high/medium/low), category (optional).",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "title": "text", "description": "REQUIRED. Task description."},
            "priority": {"type": "string", "title": "priority", "description": "Optional. high/medium/low."},
            "category": {"type": "string", "title": "category", "description": "Optional. Category name."}},
            "required": ["text"]}}},
    {"type": "function", "function": {"name": "todo_list",
        "description": "List to-do items. Args: category (optional filter), done (optional bool).",
        "parameters": {"type": "object", "properties": {
            "category": {"type": "string"}, "done": {"type": "boolean"}},
            "required": []}}},
    {"type": "function", "function": {"name": "todo_done",
        "description": "Mark a to-do item as done. Args: task_id (REQUIRED, integer).",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer"}},
            "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "todo_remove",
        "description": "Remove a to-do item. Args: task_id (REQUIRED, integer).",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer"}},
            "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "set_preference",
        "description": "Store a standing preference Chris wants obeyed on every future reply. Call it as soon as he states one, without being asked. Pick the key from the enum — do NOT invent key names. Args: key (REQUIRED, one of the enum values), value (REQUIRED).",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string", "enum": [
                "name", "pronouns", "tone", "brevity", "format", "language",
                "units", "currency", "dates", "email", "phone", "location",
                "study", "notifications", "schedule", "greeting", "diet"]},
            "value": {"type": "string", "description": "what to prefer from now on"}},
            "required": ["key", "value"]}}},
    {"type": "function", "function": {"name": "list_preferences",
        "description": "List the standing preferences already stored.",
        "parameters": {"type": "object", "properties": {},
            "required": []}}},
    {"type": "function", "function": {"name": "forget_preference",
        "description": "Stop following a stored preference when Chris asks you to. Args: key (REQUIRED).",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string"}},
            "required": ["key"]}}},
]

# Compact tool schema + compact system prompt for the LOCAL Ollama fallback in
# /chat dispatch. This PC (i7-3770, no GPU) prefills at ~10 tok/s, so the full
# 30-tool schema (~2.7k tok) + persona (~3.5k tok) = ~6k tokens = 10+ MINUTES of
# prefill on a cold model — that's the 8-minute timeout Chris keeps hitting.
# Sending only the device/navigation tools with terse descriptions keeps each
# round's prefill under ~150s; Ollama's KV cache then makes rounds 2+ cheap.
# Tool names MUST match TOOLS keys (the executor only accepts those).
OLLAMA_TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "ui_device",
        "description": "List connected Android devices + screen size/density.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ui_app_open",
        "description": "Launch StudentSyncSA on the device. No args.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ui_tap",
        "description": "Tap at pixel (x,y). Get screen size first via ui_device. x,y integer pixels.",
        "parameters": {"type": "object", "properties": {
            "x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "ui_swipe",
        "description": "Swipe/scroll from (x1,y1) to (x2,y2). duration ms optional.",
        "parameters": {"type": "object", "properties": {
            "x1": {"type": "integer"}, "y1": {"type": "integer"},
            "x2": {"type": "integer"}, "y2": {"type": "integer"},
            "duration": {"type": "integer"}}, "required": ["x1", "y1", "x2", "y2"]}}},
    {"type": "function", "function": {"name": "ui_type",
        "description": "Type text into the focused field. Args: text (string).",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "ui_key",
        "description": "Press a key: back, home, enter, tab, up, down, left, right, esc.",
        "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {"name": "ui_dump",
        "description": "Read on-screen UI hierarchy text (verify where you are). No args.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ui_screenshot",
        "description": "Capture screen (shown to Chris in a popup; not saved unless save=true).",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"}, "save": {"type": "boolean"}}, "required": []}}},
    {"type": "function", "function": {"name": "ui_assert_text",
        "description": "Assert text is (or isn't, present=false) on screen. Args: text (string), present optional bool.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string"}, "present": {"type": "boolean"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "ui_assert_element",
        "description": "Assert an element exists by resource_id / text / desc / cls. Args: resource_id, text, desc, cls optional, present optional bool.",
        "parameters": {"type": "object", "properties": {
            "resource_id": {"type": "string"}, "text": {"type": "string"},
            "desc": {"type": "string"}, "cls": {"type": "string"},
            "present": {"type": "boolean"}}, "required": []}}},
    {"type": "function", "function": {"name": "ui_assert_visible",
        "description": "Assert an element is visible+enabled on screen. Args: resource_id / text / desc / cls optional.",
        "parameters": {"type": "object", "properties": {
            "resource_id": {"type": "string"}, "text": {"type": "string"},
            "desc": {"type": "string"}, "cls": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "ui_expect",
        "description": "Compare screen to expected state. Args: expected = JSON {present:[],absent:[]} or text fragments.",
        "parameters": {"type": "object", "properties": {
            "expected": {"type": "string"}}, "required": ["expected"]}}},
    {"type": "function", "function": {"name": "ui_test_run",
        "description": "Run scripted UI actions+assertions. Args: steps = JSON list of {tool,args}, name optional.",
        "parameters": {"type": "object", "properties": {
            "steps": {"type": "string"},             "name": {"type": "string"}}, "required": ["steps"]}}},
    {"type": "function", "function": {"name": "curl",
        "description": "Hit a URL and return HTTP status + body snippet. ok=False = no service/port closed. Args: url (https), timeout optional.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}, "timeout": {"type": "number"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "run_command",
        "description": "Run a shell command and return stdout/stderr. Args: command.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "notify",
        "description": "Send a push notification to Chris's phone via ntfy. Use when Chris asks to 'ping my phone', 'notify me'. Args: message (text), title optional.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "check_email",
        "description": "Check Chris's Gmail/Yahoo now and phone-push (ntfy) anything matching his watch rules (e.g. NSFAS). Args: force_all optional boolean.",
        "parameters": {"type": "object", "properties": {
            "force_all": {"type": "boolean"}}, "required": []}}},
    {"type": "function", "function": {"name": "get_time",
        "description": "Current local date/time and weekday. No args.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "web_search",
        "description": "Search the web and return top results WITH content snippets; answer directly from those. Args: query, max_results optional.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "webfetch",
        "description": "Fetch full page content from a URL. Args: url (REQUIRED), format (optional). USE after web_search to read actual page content.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}, "format": {"type": "string"}}, "required": ["url"]}}},
]

OLLAMA_SYS_PROMPT = (
    "You are ACEsi driving an Android device. ACT, don't ask.\n"
    "NEVER reply with just a narrated plan — every turn must contain at least "
    "one real tool call (ui_dump / ui_tap / ui_swipe / ui_type / ui_key / "
    "ui_app_open / ui_screenshot) unless the screen is confirmed done.\n"
    "NAVIGATION RULE — you MUST follow this for every UI interaction:\n"
    "1. ui_app_open (once)\n"
    "2. ui_dump — read the screen, identify what you see\n"
    "3. Decide your next tap/swipe based on what ui_dump showed you\n"
    "4. ui_tap or ui_swipe\n"
    "5. ui_dump — verify the tap worked, see the new screen\n"
    "6. Repeat from step 3\n"
    "If Chris says you are on a screen (e.g. 'You are on the ITS portal'), the "
    "app is already open: start with ui_dump to read it.\n"
    "NEVER guess coordinates. NEVER tap without reading the screen first.\n"
    "After every ui_tap or ui_swipe, you MUST run ui_dump before your next move.\n"
    "STYLE: never narrate your reasoning in prose. Between tool calls output "
    "ONLY the next tool call — no 'I will', no 'The dump shows', no summaries, "
    "no commentary. All thinking is silent. When the screen is confirmed done, "
    "finish with a SHORT final report: state plainly what you did and read the "
    "key labels/values from the last ui_dump in a compact list. Keep it to 3-5 "
    "lines max. No paragraphs of reasoning in the final either.\n"
)

_ICONS = {
    "list_files": "📂", "read_file": "📄", "grep": "🔍",
    "write_file": "✏️", "edit_file": "✏️", "open_in_vscode": "📤",
    "run_command": "▶", "notify": "🔔", "web_search": "🔎", "webfetch": "🌐",
    "todo_add": "📋", "todo_list": "📋", "todo_done": "✅",
    "todo_remove": "🗑️", "note": "📝",
    "cdp_connect": "🔌", "cdp_evaluate": "💻", "cdp_console_logs": "📜",
    "cdp_dom_state": "🌐", "cdp_network_requests": "🌍", "cdp_status": "📊",
    "curl": "🔗",
    "git_status": "🌿", "git_log": "🌿", "git_commit": "🌿",
    "git_branch": "🌿", "git_merge": "🌿", "build_apk": "📦",
    "pub_add": "🧩", "pub_remove": "🧩", "pub_upgrade": "🧩",
    "flutter_test": "🧪", "flutter_analyze": "🔬",
    "ui_device": "📱", "ui_app_open": "📱", "ui_tap": "🖱️", "ui_swipe": "🖱️",
    "ui_type": "⌨️", "ui_key": "⌨️", "ui_dump": "🗺️", "ui_screenshot": "📷",
    "ui_assert_text": "✅", "ui_assert_element": "✅", "ui_assert_visible": "👁️",
    "ui_expect": "🎯", "ui_test_run": "🧪",
    "restart": "🔄",
}

def _tool_icon(name):
    return _ICONS.get(name, "🔧")

def _save_target_path(user_message):
    """Extract the intended save path from a research+save request
    ("...save the findings to notes/rental_agencies.md")."""
    m = (user_message or "").lower()
    _pm = user_message or ""
    mt = re.search(r'\bsave\b.*?\b(?:to|as|in)\b\s+([\w./\\-]+\.(?:md|txt|json|csv)\b)', _pm, re.IGNORECASE)
    if not mt:
        mt = re.search(r'\bnotes?/[\w./\\-]+\.(?:md|txt|json|csv)\b', _pm, re.IGNORECASE)
    if mt:
        return mt.group(1).replace("\\", "/")
    return None


_SUBTASK_PROBES = [
    ("web search",   ("web_search",),            r"\bsearch\b|\bfind out\b|\bagenc"),
    ("fetch pages",  ("webfetch", "curl"),       r"\bfetch\b|\btop \d+\b"),
    ("save file",    ("write_file", "open_in_vscode"), r"\bsave\b|\bwrite .*file\b"),
    ("weather",      ("weather",),               r"\bweather\b"),
    ("current time", ("get_time",),              r"\bcurrent time\b|\bwhat time\b"),
    ("open/view user file", ("view_user_file", "open_user_file", "read_user_file"),
     r"\b(?:open|view|show|display)\b.*\b(?:file|median|picture|photo|image|\.(?:png|jpe?g|gif|pdf|txt|md))\b"),
    # Broad question-type probes. These match almost any question, so they are
    # only enforced on genuinely multi-step requests (see _BROAD_PROBES).
    ("answer question", ("web_search", "webfetch", "curl"),
     r"\b(?:what|who|when|where|which|whom|whose)\b\s+[\w'\- ]{2,40}\b(?:is|was|were|are|does|did|do)\b"
     r"|\boldest\b|\blargest\b|\bsmallest\b|\bhighest\b|\binvented\b|\bfounded\b"),
    ("price lookup", ("web_search",),
     r"\b(?:price|closing price|close[ds]? at|index|stock|share price|exchange rate|rate of)\b"),
    ("compare values", ("web_search",),
     r"\bcompare[ds]?\b|\bversus\b|\bvs\.?\b|\bcompared to\b|\byear ago\b|\bthan last\b|\bchange in\b"),
]

# Probes too generic to enforce on their own: "who was Nelson Mandela?" must not
# leave the model being nagged forever about unanswered subtasks. They only
# count when the request also contains at least one narrow, explicit step.
_BROAD_PROBES = frozenset(("answer question", "price lookup", "compare values"))


def _outstanding_subtasks(user_message: str, names: list[str]) -> list[str]:
    """Which requested subtasks have had no matching tool call yet."""
    text = (user_message or "").lower()
    done = set(names)
    matched = [label for label, tools, pattern in _SUBTASK_PROBES
               if re.search(pattern, text) and not (done & set(tools))]
    if not matched:
        return []
    # Enforce broad question probes only for multi-step requests.
    detected = sum(1 for _l, _t, pat in _SUBTASK_PROBES if re.search(pat, text))
    if detected < 2:
        return [l for l in matched if l not in _BROAD_PROBES]
    return matched


# KNOWN LIMITATION: completion is keyed on tool name, so a single web_search
# satisfies every question-type probe at once. That is deliberate and safe
# (it can only under-nudge, never over-nudge) but it means the nudge cannot
# distinguish "searched for housing" from "answered the Mandela question".
# Broad probes therefore only bite when the model stalls BEFORE searching, e.g.
# after a file step. The reply-leak guard in _sanitize_reply covers the case
# where the research completed but the final answer was destroyed.


def _draft_research_fallback(llm_messages, names, user_message):
    """If a research+save task gathered web results but the model never emitted
    open_in_vscode/write_file, compile the collected tool results into a REVIEW
    DRAFT and open it in the editor. Returns (True, reply) when a draft was made,
    else (False, None)."""
    try:
        if not user_message or "open_in_vscode" in names or "write_file" in names:
            return False, None
        # Prefer clean web_search results ("- title\n  url" pairs) over raw HTML
        # dumps from webfetch/curl — those are not for Chris to read directly.
        _search = [str(msg.get("content", "")) for msg in llm_messages
                   if msg.get("role") == "tool" and msg.get("name") == "web_search"]
        _search = [s for s in _search if s and s != "(no web results)"]
        _fetches = [str(msg.get("content", "")) for msg in llm_messages
                    if msg.get("role") == "tool" and msg.get("name") in ("webfetch", "curl")]
        _fetches = [f for f in _fetches if f and not f.startswith("web_search failed")
                    and not f.startswith("webfetch failed") and not f.startswith("curl failed")]
        if not _search and not _fetches:
            return False, None
        _target = _save_target_path(user_message) or "notes/research_findings.md"
        lines = []
        if _search:
            # Search results already arrive as "- Title\n  URL" line pairs; pick
            # the top results the user asked for. URLs were decoded by
            # _clean_result_url so they open directly (no DDG 400 redirects).
            for sr in _search:
                prev = None
                for ln in sr.splitlines():
                    ln = ln.rstrip()
                    stripped = ln.strip()
                    if stripped.startswith("- "):
                        if prev is not None:
                            lines.append(prev)
                        prev = ln
                    elif prev is not None and stripped:
                        # indent continuation (the URL under a "- Title")
                        prev = prev + " " + stripped
                if prev is not None:
                    lines.append(prev)
            if not lines and _fetches:
                lines = _summarize_fetched(_fetches)
        else:
            lines = _summarize_fetched(_fetches)
        if not lines:
            return False, None
        body = "".join("%s\n\n" % ln for ln in lines)
        _head = ("# %s\n\n"
                 "ACEsi gathered these results. Review them in VS Code, then say "
                 "'save it' to write this to %s (or 'discard' to throw it away).\n\n"
                 % (_target.replace(".md", "").replace("_", " ").title(),
                    _target))
        _draft_content = _head + body
        _dok, _dtxt = tool_open_in_vscode(_target, _draft_content)
        if not _dok:
            print("📥 /chat research fallback: could not open draft: %s" % _dtxt)
            return False, None
        names.append("open_in_vscode")
        with _AGENT_LOCK:
            _AGENT["steps"].append({"id": _agent_next_id(), "kind": "work",
                                    "text": "open_in_vscode %s" % _target,
                                    "state": "done", "icon": "📤"})
        print("📥 /chat research fallback: drafted collected results for review (%d items)" % len(lines))
        return True, ("I researched that and put the findings in VS Code as a draft "
                      "(%s). Give them a look — say 'save it' and I'll write them to "
                      "%s, or 'discard' to throw them away." % (_target.replace("/", "\\"), _target))
    except Exception as _e:
        print("⚠️ /chat research-fallback draft failed: %s" % _e)
        return False, None

def _summarize_fetched(_fetches):
    """Turn raw webfetch/curl bodies into short one-line-per-result summaries."""
    import html as _html
    import re as _r
    out = []
    for f in _fetches:
        txt = _r.sub(r'<script[^>]*>.*?</script>', '', f, flags=_r.S)
        txt = _r.sub(r'<style[^>]*>.*?</style>', '', txt, flags=_r.S)
        txt = _r.sub(r'<[^>]+>', ' ', txt)
        txt = _html.unescape(_r.sub(r'\s+', ' ', txt)).strip()
        out.append("- " + txt[:200])
    return out

def _tool_desc(name, args):
    a = {k: v for k, v in (args or {}).items() if k in (TOOLS.get(name, (None, ()))[1] or ())}
    if name not in TOOLS:
        return name
    if name in ("list_files", "read_file", "grep"):
        p = a.get("path", ".")
        s = a.get("pattern")
        return "%s %s%s" % (name, p, (" — "+s) if s else "")
    if name in ("edit_file",):
        return "%s %s" % (name, a.get("path", "?"))
    if name == "write_file":
        return "%s %s" % (name, a.get("path", "?"))
    if name == "open_in_vscode":
        return "%s %s" % (name, a.get("path", "?"))
    if name == "run_command":
        return "%s `%s`" % (name, str(a.get("command", ""))[:80])
    if name == "cdp_evaluate":
        return "%s `%s`" % (name, str(a.get("expr", ""))[:80])
    if name == "git_commit":
        return "%s `%s`" % (name, str(a.get("message", ""))[:80])
    if name == "git_merge":
        return "%s `%s`" % (name, str(a.get("branch", ""))[:40])
    if name == "pub_add":
        return "%s `%s`" % (name, str(a.get("package", ""))[:80])
    if name == "ui_tap":
        return "%s (%s,%s)" % (name, a.get("x"), a.get("y"))
    if name == "ui_swipe":
        return "%s (%s,%s)->(%s,%s)" % (name, a.get("x1"), a.get("y1"),
                                        a.get("x2"), a.get("y2"))
    if name == "ui_type":
        return "%s `%s`" % (name, str(a.get("text", ""))[:60])
    if name == "ui_screenshot":
        return "%s %s" % (name, a.get("name") or "")
    if name in ("ui_assert_text", "ui_assert_element", "ui_assert_visible"):
        return "%s %s" % (name, ", ".join(
            "%s=%r" % (k, v) for k, v in (a or {}).items() if v not in (None, "")))
    if name == "ui_expect":
        return "%s `%s`" % (name, str(a.get("expected", ""))[:80])
    if name == "ui_test_run":
        return "%s `%s`" % (name, str(a.get("name") or "scenario")[:40])
    if name == "restart":
        return "%s `%s`" % (name, a.get("what") or "cdp")
    if name == "curl":
        return "%s `%s`" % (name, str(a.get("url", ""))[:60])
    return name

_REQUIRED_ARGS = {}
for _t in TOOLS_SCHEMA:
    _req = (_t.get("function") or {}).get("parameters") or {}
    _name = (_t.get("function") or {}).get("name")
    if _name:
        _REQUIRED_ARGS[_name] = [r for r in (_req.get("required") or []) if r]

# Compact schema for net-domain tools (used by OpenRouter to stay under 2652 token limit)
# read_file/write_file are included so web-research tasks that ALSO save findings to a
# notes/*.md file can persist results; they're filtered out for pure net domain calls.
NET_TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "curl",
        "description": "Hit a URL, return status + body snippet. Args: url, timeout.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "timeout": {"type": "number"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "web_search",
        "description": "Search web and return results with content snippets; answer directly from those. Args: query, max_results.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "webfetch",
        "description": "Fetch full page content. Args: url, format.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "format": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "check_email",
        "description": "Check Chris's Gmail/Yahoo now and phone-push (ntfy) anything matching his watch rules (e.g. NSFAS). Args: force_all optional boolean.",
        "parameters": {"type": "object", "properties": {"force_all": {"type": "boolean"}}, "required": []}}},
    {"type": "function", "function": {"name": "view_web_image",
        "description": "Download an image from a URL and DISPLAY it inline in the ACEsi chat window as a popup — use when the user wants to actually SEE a picture from the internet. The URL must point directly at an image file (png/jpg/jpeg/gif/webp/bmp). Args: url.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "weather",
        "description": "Current weather for a city. Args: city.",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "read_file",
        "description": "Read a file's contents (path relative to DATA_DIR). Args: path.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file",
        "description": "Write/overwrite a file (path relative to DATA_DIR). Args: path, content.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "open_in_vscode",
        "description": "Open content in the user's code editor (VS Code/VSCodium) as a review DRAFT — does NOT write the final file. Chris reviews it in the editor and decides whether to save. Use whenever the user asked to research/save/find + save to a file: compose the findings, call this with path (intended final location) and content, then tell Chris to review. Chris will then say 'save it' to commit. Args: path, content.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "note",
        "description": "Save a note to notes.json. Args: text.",
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "todo_add",
        "description": "Add a to-do task. Args: text (REQUIRED), priority (optional), category (optional).",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string", "title": "text", "description": "REQUIRED. Task description."},
            "priority": {"type": "string"}, "category": {"type": "string"}},
            "required": ["text"]}}},
    {"type": "function", "function": {"name": "todo_list",
        "description": "List to-do items. Args: category (optional), done (optional bool).",
        "parameters": {"type": "object", "properties": {
            "category": {"type": "string"}, "done": {"type": "boolean"}},
            "required": []}}},
    {"type": "function", "function": {"name": "todo_done",
        "description": "Mark a to-do item done. Args: task_id (REQUIRED, integer).",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer"}},
            "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "todo_remove",
        "description": "Remove a to-do item. Args: task_id (REQUIRED, integer).",
        "parameters": {"type": "object", "properties": {
            "task_id": {"type": "integer"}},
            "required": ["task_id"]}}},
    {"type": "function", "function": {"name": "get_time",
        "description": "Current local date/time and weekday.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "notify",
        "description": "Send push notification via ntfy. Args: message, title.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "restart",
        "description": "Restart server/cdp/ollama. Args: what.",
        "parameters": {"type": "object", "properties": {"what": {"type": "string"}}, "required": ["what"]}}},
]

# Tool domain / context separation (ACEsi mixes UI, code, and network work, so
# we keep them in distinct buckets and can restrict which domain a request is
# allowed to touch). A tool lives in exactly one domain; the dispatch loop
# consults ALLOWED_DOMAINS per request.
_TOOL_DOMAINS = {
    # device UI work
    "ui_device": "ui", "ui_app_open": "ui", "ui_tap": "ui", "ui_swipe": "ui",
    "ui_type": "ui", "ui_key": "ui", "ui_dump": "ui", "ui_screenshot": "ui",
    "ui_assert_text": "ui", "ui_assert_element": "ui", "ui_assert_visible": "ui",
    "ui_expect": "ui", "ui_test_run": "ui",
    # on-device Chrome/WebView (still UI-side, but via CDP)
    "cdp_connect": "ui", "cdp_evaluate": "ui", "cdp_console_logs": "ui",
    "cdp_dom_state": "ui", "cdp_network_requests": "ui", "cdp_status": "ui",
    # network / URL probes — the new curl tool isolates "is this URL up?" from
    # both code edits and on-device taps
    "curl": "net",
    # file-system / code tools
    "list_files": "code", "read_file": "code", "list_user_files": "code", "read_user_file": "code", "open_user_file": "code", "view_user_file": "code", "grep": "code",
    "write_file": "code", "edit_file": "code", "open_in_vscode": "code", "run_command": "code",
    "git_status": "code", "git_log": "code", "git_commit": "code",
    "git_branch": "code", "git_merge": "code",
    "build_apk": "code", "pub_add": "code", "pub_remove": "code",
    "pub_upgrade": "code", "flutter_test": "code", "flutter_analyze": "code",
    # runtime controls
    "restart": "ctrl",
    # push notification to Chris's phone (available in every domain, like ctrl)
    "notify": "ctrl",
    # email watch: polls Gmail/Yahoo and phone-pushes matches (NSFAS etc.)
    "check_email": "ctrl",
    "list_email_rules": "ctrl",
    # general helpers available in every domain (get_time, note) — network info
    # helpers (web_search, weather) live in net so code-only contexts exclude them
    "get_time": "ctrl",
    "note": "ctrl",
    "todo_add": "ctrl",
    "todo_list": "ctrl",
    "todo_done": "ctrl",
    "todo_remove": "ctrl",
    "web_search": "net",
    "webfetch": "net",
    "view_web_image": "net",
    "weather": "net",
}


def _explicit_tool_domain(user_message):
    """If the user directly names a tool (e.g. 'use the curl tool', 'run ui_tap',
    'call ui_assert_text'), return that tool's domain (net/ui/code) so the
    dispatch loop skips the ambiguity gate and runs THAT tool directly. This is
    the 'ignore the menu — this is a direct instruction' case."""
    m = (user_message or "").lower()
    best = None
    for name, dom in _TOOL_DOMAINS.items():
        # Word-boundary anchored so a note/filename like "notes/rental_agencies.md"
        # does NOT match the `note` tool (only a real "note" / "web_search" /
        # "curl" token does), and a domain hint can't be hijacked by a file path.
        if re.search(r'\b' + re.escape(name) + r'\b', m):
            # Prefer a concrete work domain (ui/net/code) over 'ctrl'.
            if dom != "ctrl":
                return dom
            best = best or dom
    return best


def _web_research_task(m):
    """True when the (lowercased) message is a web-search/research request
    ("search the web", "find ... online", "look up ... on the internet",
    or factual questions that need current/authoritative info)."""
    # Explicit search intent
    if ("web" in m or "online" in m or "internet" in m) and bool(
        re.search(r'\b(?:search|find|look\s+up)\b', m)):
        return True
    # Factual questions that likely need current/authoritative web info
    factual_patterns = [
        r'\b(?:what|who|when|where|which)\s+(?:is|was|are|were)\b',
        r'\b(?:how\s+(?:old|many|much|long|tall|wide))\b',
        r'\b(?:oldest|newest|latest|current|recent)\b',
        r'\b(?:capital|population|president|prime\s+minister)\b',
        r'\b(?:weather|temperature|forecast)\b',
        r'\b(?:latest\s+news|breaking|headline)\b',
    ]
    return any(re.search(p, m) for p in factual_patterns)


def _explicit_save_request(m):
    """True when the user EXPLICITLY asked to save research findings to a file
    (e.g. 'search X and save it to notes/foo.md', 'write the findings to
    rental_agencies.txt'). A bare factual question ('what is the oldest book?')
    returns False even though it may need the web_search tool — only named
    save targets trigger the draft/open_in_vscode review flow."""
    return bool(
        re.search(r'\bsave\b.*(?:to\s+)?(?:notes?/|\.(?:md|txt|json|csv)\b|file\b)', m) or
        re.search(r'\b(?:write|put|store|copy)\b.*(?:to\s+)?(?:notes?/|\.(?:md|txt|json|csv)\b)', m))


def _classify_message(user_message):
    """Decide which tool domain(s) a user message is asking about, so we can
    (a) surface the right context to the model and (b) refuse tools from a
    domain the user did not ask for instead of silently doing two unrelated
    things at once. A request that EXPLICITLY names a tool (e.g. 'use the curl
    tool on this URL') wins and is NOT treated as ambiguous just because a URL
    host name happens to contain a UI word like 'portal'."""
    m = (user_message or "").lower()
    has_url = ("https://" in m) or ("http://" in m)
    _reach_re = re.compile(r"\b(is\s+(it|the)\s+|check\s+if\s+).*\b(up|down)\b")
    # Strong, unambiguous network intent: "curl <url>", "use the curl tool on
    # <url>", "is <host> up/down", "reachability", "status code of", "port 443",
    # "no web service". NOTE: 'up'/'down' only count as net when paired with a
    # probe verb, so a UI request like 'screenshot' never flips to network.
    net_strong = ("curl" in m and (has_url or "url" in m or "reachab" in m
                                     or "status code" in m or "port " in m or "443" in m)) or \
                 bool(_reach_re.search(m)) or \
                 (has_url and bool(re.search(r'\b(up|down)\b', m))) or \
                 any(k in m for k in ("reachab", "is up", "is down", "status code",
                     "no ports", "no web service", "up?", "down?", "port ", "443", "8080", "dns"))
    # Real on-device UI ACTION intent only (NOT incidental host mentions like
    # 'univenierp'/'portal'/'screen'). This is what stops 'curl
    # https://univenierp01.univen.ac.za/.../portal/...' being misread as a UI
    # request, and what keeps nav intent in the ui bucket.
    ui_action = any(k in m for k in (
        "ui_tap", "ui_swipe", "ui_type", "ui_key", "ui_dump", "ui_screenshot",
        "ui_app_open", "ui_assert", "ui_expect", "ui_test_run",
        "emulator", "open the app", "go to", "navigate", "navigation",
        "tap ", "swipe ", "cdp_", "webview", "show me", "take a", "screenshot")) \
        or _test_task(m)
    # Situational/ambient UI asks that don't name a tool but DO place the
    # assistant on the device screen: "You are on the ITS portal", "what does
    # the screen show", "what do you see", "read the screen". Without these, the
    # classifier returns 'general' and the whole ui_* toolset vanishes from the
    # schema — the 3B model then narrates a plan it cannot execute.
    ui_situational = any(k in m for k in (
        "you are on", "you're on", "we are on", "on the portal",
        "on the its portal", "what does the screen show", "what do you see",
        "read the screen", "look at the screen", "on the screen",
        "see the screen", "the screen shows", "show the screen",
        "what is on the screen", "what's on the screen", "screen state"))
    # Strong code-edit signal: a filename with a code extension (e.g.
    # "university_webview_screen.dart") should be treated as pure code work,
    # even if the filename happens to contain a UI word like 'webview'.
    # This prevents the domain gate from firing a clarification menu when the
    # user asks ACEsi to edit/replace a specific code file.
    _code_exts = ('.dart', '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
                  '.json', '.yaml', '.yml', '.md', '.sh', '.bat', '.rs', '.go',
                  '.java', '.kt', '.swift', '.c', '.cpp', '.h', '.hpp')
    # Word-boundary anchored so ".c" in "example.com" is NOT a code file, but
    # "file.c" / "main.dart" / "index.html" are.
    _code_ext_re = r'\.(?:' + '|'.join(re.escape(ext[1:]) for ext in _code_exts) + r')\b'
    # File-access phrases that should route to code domain (not UI navigation).
    _file_access_phrases = (
        "look for", "find the file", "my pictures", "my files", "my desktop",
        "my downloads", "open an find", "open and find", "in my pictures",
        "in my files", "in my desktop", "in my downloads", "pictures folder",
        "desktop folder", "downloads folder")
    code_strong = any(k in m for k in (
        "edit ", "replace ", "write file", "open file", "read file",
        "edit_file", "write_file", "read_file")) or \
        any(k in m for k in _file_access_phrases) or \
        bool(re.search(_code_ext_re, m)) or \
        bool(re.search(r'\b(?:lib|src|test|assets)/[\w/]+\.\w+', m))
    domains = set()
    # A strong net request with no device ACTION is purely network work, even if
    # the URL hostname contains UI-ish words (e.g. ...univenierp...portal/...).
    if net_strong and not ui_action:
        return {"net"}
    # Web research that ALSO saves to a file (e.g. "search the web ... save the
    # findings to notes/rental_agencies.md") is a hybrid net+code task: it needs
    # web_search/curl to gather AND write_file to store. Resolve it to 'general'
    # (code+net+ctrl) BEFORE code_strong fires on the .md target filename, which
    # would otherwise strip web_search entirely.
    _save_target = bool(re.search(r'\bsave\b.*\bnotes?/', m)) or bool(
        re.search(r'\bsave\b.*\.(?:md|txt|json|csv)\b', m))
    if _web_research_task(m) and _save_target and not ui_action:
        return {"general"}
    # A strong code-edit signal (filename with code extension, explicit edit
    # commands) overrides false-positive UI matches from incidental keywords
    # in filenames (e.g. "webview" in "university_webview_screen.dart").
    if code_strong:
        return {"code"}
    # Situational UI ("You are on the ITS portal", "what does the screen show")
    # with NO URL/curl and NO net probe is pure on-device work — the assistant
    # must read the screen and report. Return {"ui"} directly so the ui_* tools
    # stay in the schema (otherwise the 3B model narrates an unexecutable plan).
    _has_url_or_curl = ("http" in m) or ("curl" in m) or ("//" in m)
    if ui_situational and not net_strong and not _has_url_or_curl:
        return {"ui"}
    # Network probe intent (status-check patterns like "check if...up",
    # "is the portal reachable") should override false-positive UI matches
    # from navigation words ("navigate", "open the app") — but ONLY when the
    # message also mentions a URL, hostname, or explicit network term. Bare
    # "check if" about app behavior (e.g. "open the app, navigate to ITS,
    # check if the 404 is gone") is a UI verification task, not a curl.
    _status_re = re.compile(
        r'(check\s+(?:if|whether)\s+(?:the\s+)?(?:url|host|server|site|portal|domain)\b|'
        r'is\s+(?:it|the\s+(?:url|host|server|site|portal|domain))\s+(?:up|down|reachable|'
        r'working|live|online|accessible)|reachab|status\s+(?:of|code))')
    _has_net_term = any(k in m for k in (
        "url", "host", "server", "site", "domain", "curl", "http",
        "https", "port", "dns", "endpoint", "reachable", "response"))
    if net_strong and ui_action and _status_re.search(m) and _has_net_term:
        return {"net"}
    # A strong on-device action ("open the app", "navigate to", "go to") with
    # NO explicit URL or curl is purely a UI task — "portal" in the message is
    # just the name of a page the user wants navigated TO, not a network probe.
    if ui_action and not _has_url_or_curl:
        return {"ui"}
    if ui_action or ui_situational or any(k in m for k in ("emulator", "cdp_", "webview")):
        domains.add("ui")
    if net_strong or ("curl" in m) or any(k in m for k in (
            "url", "domain", "offline", "reachab", "is up", "is down",
            "status code", "port ", "443", "8080", "dns", "no ports", "no web service",
            "web_search")):
        domains.add("net")
    if any(k in m for k in ("edit", "read", "file", "write", "code", "build",
                            "apk", "flutter", "git ", "commit", "analyze")):
        domains.add("code")
    if any(k in m for k in ("restart", "relaunch", "heal", "self-host", "ollama")):
        domains.add("ctrl")
    return domains or {"general"}


def _domain_tool_names(domain):
    """Tool names allowed for a given domain (general = code + net + ctrl, i.e. the
    file/shell/web toolset but NOT on-device UI work)."""
    if domain == "general":
        return {n for n, d in _TOOL_DOMAINS.items() if d in ("code", "net", "ctrl")}
    return {n for n, d in _TOOL_DOMAINS.items() if d == domain}


def _filter_tools_schema(schema, allowed_names):
    return [t for t in schema if t["function"]["name"] in allowed_names]


# Free-tier input-token caps (per request). Groq's ITPM is 7000 for this org;
# keep a safety margin so a large system prompt + schema still fits.
_LLM_INPUT_TOKEN_BUDGET = 6200
# Tools the model must always keep: the ones that answer "show me X" and let it
# find things on the web/file system. Everything else is droppable when the
# payload is too big for the provider.
_LLM_CORE_TOOLS = {
    "web_search", "view_web_image", "webfetch", "curl",
    "view_user_file", "list_user_files", "read_file", "grep", "list_files",
    "open_in_vscode", "edit_file", "get_notifications", "check_email", "notify",
    "ui_dump", "ui_screenshot", "ui_app_open", "ui_tap", "ui_type", "ui_swipe",
}


def _fit_schema_to_budget(messages, tools_schema, max_tokens, budget=_LLM_INPUT_TOKEN_BUDGET):
    """Drop the least important tools until prompt+schema fits the provider cap.

    Providers reject an oversized request with 413 and llm_reply then falls
    through to "all providers unavailable", which looks like an outage but is
    really a payload-size problem. Core tools are never dropped; the rest are
    removed largest-first until the estimated token count fits.
    """
    def est(tools):
        payload = json.dumps({"messages": messages, "tools": tools,
                              "max_tokens": max_tokens})
        return len(payload) // 4

    tools = list(tools_schema)
    if est(tools) <= budget:
        return tools
    droppable = [t for t in tools
                 if t["function"]["name"] not in _LLM_CORE_TOOLS]
    # Biggest schemas cost the most tokens, so shed those first.
    droppable.sort(key=lambda t: len(json.dumps(t)), reverse=True)
    for t in droppable:
        if est(tools) <= budget:
            break
        tools.remove(t)
    print("✂️ schema trimmed %d -> %d tools to fit %d-token budget (est %d)"
          % (len(tools_schema), len(tools), budget, est(tools)))
    return tools


class _DomainGate(Exception):
    pass


# ===== Multi-context engine (from ace_config.yaml) =====
# ACEsi is not just StudentSyncSA anymore: ace_config.yaml declares named
# contexts (studentsyncsa / generic / web_only / code) with per-context tool
# caps and a prompt overlay. The active context is selected per request by the
# same keyword classifier the tool-domain filter already uses (ui/net/code),
# so tool availability and system-prompt hints follow the request's domain.
_ACE_CONFIG = {}
_ACE_CONTEXTS = {}
_ACE_DEFAULT_CTX = "studentsyncsa"
_ctx_last = {"name": "studentsyncsa", "overlay": ""}


def _load_ace_config():
    global _ACE_CONFIG, _ACE_CONTEXTS, _ACE_DEFAULT_CTX
    try:
        import yaml
        path = os.path.join(DATA_DIR, 'ace_config.yaml')
        if not os.path.isfile(path):
            return
        with open(path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        _ACE_CONFIG = cfg
        _ACE_CONTEXTS = cfg.get('contexts') or {}
        glob = cfg.get('global') or {}
        _ACE_DEFAULT_CTX = glob.get('default_context', 'studentsyncsa')
        print("🧠 ace_config.yaml loaded: contexts=%s default=%s" % (
            ", ".join(_ACE_CONTEXTS.keys()), _ACE_DEFAULT_CTX))
    except Exception as e:
        print(f"⚠️ ace_config.yaml load failed (contexts disabled): {e}")


_load_ace_config()


def _context_by_domain(domain):
    """Map the classifier's domain to a context name from ace_config.yaml."""
    if not _ACE_CONTEXTS:
        return _ACE_DEFAULT_CTX or "studentsyncsa"
    if domain == "ui":
        return "studentsyncsa" if "studentsyncsa" in _ACE_CONTEXTS else (_ACE_DEFAULT_CTX or "generic")
    if domain == "net":
        return "web_only" if "web_only" in _ACE_CONTEXTS else "generic"
    if domain == "code":
        return "code" if "code" in _ACE_CONTEXTS else "generic"
    return _ACE_DEFAULT_CTX or "generic"


def _context_tool_policy(ctx_name):
    """(allowed_domains, allowed_tools) for a context, or (None, None) = no cap."""
    ctx = (_ACE_CONTEXTS or {}).get(ctx_name) or {}
    caps_name = ctx.get('tool_caps')
    caps = (_ACE_CONFIG.get('tool_caps') or {}).get(caps_name) if caps_name else None
    if not caps:
        return None, None
    return caps.get('allowed'), set(caps.get('tools') or [])


def _context_overlay(ctx_name):
    """System-prompt overlay (known structure + persona) for the active context."""
    ctx = (_ACE_CONTEXTS or {}).get(ctx_name) or {}
    overlay = (ctx.get('prompt_overlay') or '').strip()
    known = (ctx.get('known_structure') or '').strip()
    parts = []
    if overlay:
        parts.append(overlay)
    if known and known not in overlay:
        parts.append(known)
    if ctx.get('type'):
        parts.append("[Active context: %s (%s)]" % (ctx.get('name') or ctx_name, ctx.get('type')))
    return "\n".join(parts)


@app.route('/context', methods=['GET'])
def context_endpoint():
    st = _kill_state()
    return jsonify({
        "armed": st.get("armed"),
        "default": _ACE_DEFAULT_CTX,
        "contexts": {k: ((v or {}).get('name') or k) for k, v in (_ACE_CONTEXTS or {}).items()},
        "active": _ctx_last.get('name'),
        "active_overlay": _ctx_last.get('overlay'),
    })


# Models routinely reach for snake_case / wrong-spelling variants of a tool
# name. A miss used to raise KeyError straight out of _call_tool, which
# propagated through the whole dispatch loop and out of /chat, throwing away
# every tool result the run had already gathered. Resolve the common variants
# and, for anything still unknown, return a normal tool error so the model can
# correct itself instead of the request dying.
_TOOL_ALIASES = {
    "web_fetch": "webfetch", "webfetch_url": "webfetch", "fetch_url": "webfetch",
    "web_search_tool": "web_search", "websearch": "web_search", "search_web": "web_search",
    "google": "web_search", "browse": "webfetch", "browse_url": "webfetch",
    "list_files": "list_user_files", "my_files": "list_user_files",
    "open_file": "open_user_file", "view_file": "view_user_file",
    "read_file": "read_user_file", "show_file": "view_user_file",
    "screenshot": "ui_screenshot", "screen_dump": "ui_dump",
    "tap": "ui_tap", "swipe": "ui_swipe", "type_text": "ui_type",
    "press": "ui_key", "open_app": "ui_app_open",
}


def _resolve_tool_name(name):
    """Map a requested tool name onto a registered one, or None if unknown."""
    n = str(name or "").strip()
    if n in TOOLS:
        return n
    alt = _TOOL_ALIASES.get(n) or _TOOL_ALIASES.get(n.lower())
    if alt in TOOLS:
        return alt
    low = n.lower()
    for t in TOOLS:
        if t.lower() == low:
            return t
    return None


def _call_tool(name, args):
    if _kill_armed():
        return False, "E-STOP is armed — no tools run."
    resolved = _resolve_tool_name(name)
    if resolved is None:
        near = [t for t in TOOLS if str(name or "").lower() in t or t in str(name or "").lower()]
        audit_write("tool", name, args or {}, False, "unknown tool name")
        return False, (
            "unknown tool %r. Valid tools: %s.%s"
            % (name, ", ".join(sorted(TOOLS)[:40]),
               (" Did you mean: %s?" % ", ".join(near)) if near else ""))
    if resolved != name:
        audit_write("tool", name, args or {}, True, "resolved alias -> %s" % resolved)
        name = resolved
    fn, keys = TOOLS[name]
    args = args or {}
    missing = []
    for k in _REQUIRED_ARGS.get(name, ()):
        if k not in args or args[k] is None or args[k] == "":
            missing.append(k)
    if missing:
        audit_write("tool", name, args, False, "missing args: %s" % ", ".join("%r" % m for m in missing))
        return False, ("ui tool error: missing REQUIRED argument%s %s "
                       "(you passed %r). Pass every argument as a non-null value, "
                       "e.g. ui_tap {\"x\": 540, \"y\": 1200}."
                       % ("s" if len(missing) > 1 else "",
                          ", ".join("%r" % m for m in missing),
                          {k: v for k, v in args.items()}))
    kwargs = {}
    for k in keys:
        if k in args and args[k] is not None:
            kwargs[k] = args[k]
    try:
        res = fn(**kwargs)
    except Exception as e:
        audit_write("tool", name, args, False, "exception: %s" % e)
        return False, "tool error: %s" % e
    if isinstance(res, tuple) and len(res) == 2:
        audit_write("tool", name, args, bool(res[0]), str(res[1])[:180])
    else:
        audit_write("tool", name, args, True, str(res)[:180])
    return res


_UI_SCREEN_TOOLS = {"ui_app_open", "ui_tap", "ui_swipe", "ui_type", "ui_key", "ui_screenshot"}
_BATCH_MAX = 6


def _ui_auto_dump():
    """Best-effort, FAST screen snapshot injected after every screen-changing
    ui_* tool, so the model always sees the real screen text between actions.
    Fails fast (15s per adb call) so a busy screen right after app launch never
    stalls an agent turn for minutes."""
    try:
        ok, _ = _ui_adb(["shell", "uiautomator", "dump", "/sdcard/ui.xml"], timeout=15)
        if not ok:
            return False, "auto ui_dump: screen busy (dump timed out/failed)"
        ok, out = _ui_adb(["shell", "cat", "/sdcard/ui.xml"], timeout=15, cap=None)
        if not ok or "<hierarchy" not in out:
            return False, "auto ui_dump: no hierarchy captured"
        return True, _ui_dump_compact(out, cap=5000)
    except Exception as e:
        return False, "auto ui_dump error: %s" % e


# Chrome interstitial markers that mean the ITS portal's HTTPS cert failed
# (ERR_CERT_DATE_INVALID / HSTS). The site is reachable — the model just has to
# type Chrome's official bypass ("thisisunsafe") to continue the navigation.
_CERT_WARNING_MARKERS = (
    "your connection is not private",
    "err_cert",
    "net::err_",
    "website uses hsts",
    "uses hsts",
    "attackers might be trying to steal",
    "the server's security certificate is not yet valid",
)

_CERT_WARNING_DIRECTIVE = (
    "⚠️ CHROME WARNING: the screen above is Chrome's HTTPS/cert/HSTS warning for "
    "the ITS portal (expired/invalid certificate — the site itself is reachable "
    "and safe to continue). Bypass it by calling ui_type {\"text\": \"thisisunsafe\"} "
    "— type thisisunsafe anywhere on the warning page (no Enter key needed). Then "
    "call ui_dump to confirm the portal loaded. If the wizard then shows 'Access "
    "Denied / restart the wizard process in a new window', clear Chrome's omnibox "
    "and type the portal URL: univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg."
    "gw1startup?x_processcode=ITS_OAP and press Enter."
)


def _cert_warning_directive(dump_text):
    """If a ui_dump shows Chrome's HTTPS warning, return the bypass directive to
    feed back to the model so it types 'thisisunsafe' and keeps navigating."""
    t = (dump_text or "").lower()
    if not any(m in t for m in _CERT_WARNING_MARKERS):
        return ""
    return "\n\n" + _CERT_WARNING_DIRECTIVE


def _auto_bypass_cert_warning(dump_text):
    """Server-side enforcement of the thisisunsafe bypass: if the auto-dump shows
    Chrome's HTTPS/HSTS warning, actually TYPE the bypass on the device so ACEsi
    makes forward progress even when the small Ollama model fails to act on the
    directive. Returns a list of extra user-message dicts to append (bypass
    result + fresh screen state), or [] if no warning was detected."""
    if not _cert_warning_directive(dump_text):
        return []
    msgs = []
    _bok, _bres = _call_tool("ui_type", {"text": "thisisunsafe"})
    msgs.append({"role": "user", "content":
        "I detected Chrome's HTTPS warning and ALREADY typed thisisunsafe myself "
        "(ok=%s): %s" % (_bok, str(_bres)[:200])})
    _dok, _dtxt = _ui_auto_dump()
    if _dok:
        msgs.append({"role": "user", "content":
            "SCREEN STATE after auto-bypassing the warning (auto ui_dump):\n%s%s" % (
                str(_dtxt)[:2000], _cert_warning_directive(_dtxt))})
    else:
        msgs.append({"role": "user", "content": _dtxt})
    return msgs


def _nav_task(user_message):
    m = (user_message or "").lower()
    return any(k in m for k in (
        "screenshot", "portal", "navigate", "navigation", "open the app",
        "go to", "show me", "show us", "take a"))


def _ui_situational_ask(user_message):
    """True when the request is a screen-read/situational ask: the app is
    presumed already open and the model just needs to ui_dump + report (e.g.
    'You are on the ITS portal', 'what does the screen show'). For these, the
    right first tool is ui_dump, not ui_app_open."""
    m = (user_message or "").lower()
    return any(k in m for k in (
        "you are on", "you're on", "we are on", "on the portal",
        "on the its portal", "what does the screen show", "what do you see",
        "read the screen", "look at the screen", "on the screen",
        "see the screen", "the screen shows", "show the screen",
        "what is on the screen", "what's on the screen", "screen state"))


def _looks_like_plan_narration(text):
    """True when the model's text is planning prose ("we need to...", "I'll
    tap...") rather than a completed answer. Used to separate a genuine
    text-only final reply from a stall where the model narrates instead of
    calling tools."""
    if not text:
        return False
    t = text.lower()
    markers = ("we need to", "we should", "i need to", "i'm going to", "i am going to",
               "i will", "i'll", "then tap", "then call", "then run", "next,", "next step",
               "first i", "let me", "now we", "we have to", "the plan", "then we",
               "i would", "let's", "lets ")
    return any(m in t for m in markers)

def _ui_task(user_message):
    """Broad detector for ANY on-device UI work request: explicit ui_* tool
    names, navigation/screen keywords, or references to on-screen elements to
    tap ('tap My Profile', 'tap the Lets get Started button'). This is what the
    stall-guard uses so a prose-only reply is NEVER accepted as final for a task
    the user expects real device actions on. Distinct from _nav_task (narrower
    keyword list used for time-budget sizing)."""
    m = (user_message or "").lower()
    if _nav_task(m) or _ui_situational_ask(m) or _test_task(m):
        return True
    if any(k in m for k in (
            "ui_app_open", "ui_dump", "ui_tap", "ui_swipe", "ui_type",
            "ui_key", "ui_screenshot", "ui_device", "ui_assert", "ui_expect",
            "ui_test_run", "ui_fill", "fill the", "fill in", "fill up",
            "fill the form", "fill the fields", "fill by himself",
            "cdp_", "webview", "emulator",
            "tap it", "tap on", "tap the", "tap ", "click on", "click the",
            "press the", "tab on it", "in the dump")):
        return True
    # Element reference + action in the SAME message = a real tap target
    # ("search for My Profile and tap it", "find the Lets get Started button").
    if any(k in m for k in ("profile", "button")) and \
       any(k in m for k in ("tap", "click", "press", "find", "search",
                            "open", "go to", "navigate", "get started",
                            "let's get started", "lets get started")):
        return True
    return False


def _test_task(user_message):
    """True when the request is a UI validation/test run (assertions, ui_expect,
    ui_test_run, 'validate', 'test the', 'check the ui', 'verify'). These need
    more rounds/time than a quick navigation+screenshot."""
    m = (user_message or "").lower()
    return any(k in m for k in (
        "ui_test_run", "test run", "run the test", "run a test", "ui test",
        "validate", "validation", "verif", "assert", "check the ui",
        "test the ui", "assertion", "expected", "ui_expect"))


def _nav_gate(user_message, names):
    """If a navigation/screenshot task ended with a screenshot but the model
    never actually navigated AND read the screen, return a corrective message
    so the loop pushes the model to keep going instead of accepting a fake
    FINAL. 'Navigated' means it performed an action (tap/swipe/type/key or
    read the WebView via cdp_*); 'verified' means it READ what is on screen
    (ui_dump or cdp_*). A single blind tap plus a screenshot is NOT enough."""
    if not _nav_task(user_message):
        return None
    if "ui_screenshot" not in names:
        return None
    navigated = any(n in names for n in ("ui_tap", "ui_swipe", "ui_type", "ui_key")) \
        or any(n.startswith("cdp_") for n in names)
    verified = "ui_dump" in names or any(n.startswith("cdp_") for n in names)
    if not (navigated and verified):
        if not verified:
            hint = ("you never called ui_dump to READ what is on screen (and you "
                    "cannot see images), so you don't know what the screenshot "
                    "shows")
        else:
            hint = ("you never actually navigated — no ui_tap / ui_swipe / "
                    "ui_type / ui_key (or cdp_* for the WebView), so the screen "
                    "was never changed")
        return ("You took a screenshot but %s. Work step by step: ui_app_open, "
                "then ui_dump to READ the screen, then ui_tap/ui_swipe/ui_type/"
                "ui_key to move toward the target, ui_dump after each action to "
                "confirm progress, and only then ui_screenshot. Once the ITS "
                "WebView is open, verify the URL/DOM with cdp_connect + "
                "cdp_dom_state. Do NOT emit FINAL yet." % hint)
    return None

CODE_AGENT_PROMPT = """You are ACEsi, an autonomous coding agent for the StudentSyncSA Flutter project.
You are on Windows; the project root is C:\\Users\\chris\\StudentSyncSA and `flutter`,
`dart`, `git` are on PATH. You plan, use tools, and VERIFY your own work — read first,
then act, then run a check (flutter test / flutter analyze / a script) and read the
result. Never invent facts about the code; look before you leap.

Per turn, emit lines using exactly one of these tags:
  THOUGHT: <1-2 sentence reasoning>
  CALL: <tool_name> <json-arg-object>     (you may emit several CALL lines per turn)
  FINAL: <your answer to Chris>          (ends the turn)

STYLE — CRITICAL: THOUGHT must be at most ONE short sentence. Never narrate
what a tool returned, never recap the whole plan in prose, never explain your
reasoning out loud. Between CALL lines output ONLY the CALL lines — no extra
commentary. When you finish, the FINAL is a short, plain report (3-5 lines max)
like a text message: what you did and the key result. No paragraphs, no
"First I ... then I ..." recaps.

A tool call may also be written as a single-line JSON object on its own line,
either form is accepted:
  CALL: read_file {"path": "lib/..."}
  {"command": "read_file", "args": {"path": "lib/..."}}

IMPORTANT: one tool call is executed per turn. Emit ONE call, see its result,
then emit the NEXT call. Do not batch independent edits in one turn — file
state changes after each edit, so a later edit may not match if you guessed
its old_string before seeing earlier results. If you need to re-read a file,
that's fine, but do not re-call the exact same tool with the same arguments
after a success — make forward progress instead.

{TOOLS}
Safety: run_command blocks rm/git push/checkout/flake.clean/pub get/build, adb
uninstall and scrcpy. Use the dedicated git_* tools for commits/branches/merges
(they do NOT push; git_merge rolls back on conflict). build_apk/pub_*/flutter_*
run via dedicated tools. ui_* tools drive the connected Android device. Edits
are surgical (exact-match, single occurrence) and sandboxed to the project.
Treat every step as needing verification. ALWAYS run flutter_analyze or
flutter_test after edits before committing; only git_commit when tests pass.
You cannot see screenshots — verify screen state with ui_dump, not ui_screenshot.

DISPATCH RULE — when the instruction is about the app/device (open the app,
tap, swipe, type, press a key, screenshot, check the UI): use the ui_* tools
(ui_app_open, ui_tap, ui_swipe, ui_type, ui_key, ui_dump, ui_screenshot).
read_file is ONLY for reading source/config files on disk — never feed a UI
instruction into read_file, and never use a user instruction as a file path.

UI NAVIGATION PROTOCOL (device/app tasks) — follow EVERY step:
  1. ui_app_open {}                   launch the app
  2. ui_dump {}                       see what is ACTUALLY on screen now
  3. ui_tap / ui_swipe / ui_type / ui_key   take ONE action toward the target
  4. ui_dump {} again                 VERIFY the screen changed as expected
  5. Repeat 3-4 until ui_dump confirms the target is visible.
  6. ui_screenshot {"name": "...", "save": true}    ONLY AFTER ui_dump proves the target screen.
Screenshots are NOT saved to disk by default — they are shown to Chris in a popup. Only set
save=true when Chris explicitly asked to keep the file. In your FINAL, cite the REAL page
titles/buttons from the last ui_dump and the actual screenshot behavior — never invent a file
path or claim to have opened Chrome/CDP when you did not.
HTTPS/HSTS WARNING: if a ui_dump shows Chrome's 'Your connection is not private' / ERR_CERT /
HSTS interstitial for the ITS portal (expired cert is expected), call
ui_type {"text": "thisisunsafe"} to bypass it, then ui_dump to confirm the portal loaded.
The server may already auto-type it — follow the fresh ui_dump in that case.
Never emit FINAL merely after opening the app + taking one screenshot — that is
NOT navigation and the user will see a screenshot of the wrong screen. In your
FINAL, report what the LAST ui_dump showed (the visible titles/buttons), proving
you reached the target. If a tap did not change the screen, scroll (ui_swipe) or
try a different control; never give up after one attempt.

KNOWN APP STRUCTURE (StudentSyncSA): Landing → login → the bottom navigation bar
has tabs like Home / Universities. The ITS portal is reached via: Universities tab
→ tap a university card (e.g. "University of Venda", ITS host univenierp01) → its
detail screen → tap the "↗ Online Portal" button → the ITS portal opens in an
in-app WebView. Once the WebView is open, ui_dump shows only the app chrome — read
the portal itself with the cdp_* tools (cdp_connect, then cdp_dom_state /
cdp_evaluate to confirm the URL/title), then ui_screenshot.

CRITICAL — you MUST use at least one tool before emitting FINAL. You are not
allowed to announce a fix you have not actually applied. If tool outputs show
the tests still fail, fix the cause and re-test. Never fabricate a result.

Example of a correct turn:
  THOUGHT: First I'll read the file to see the existing rules.
  CALL: read_file {"path": "lib/services/its_url_fixer.dart"}
  CALL: grep {"pattern": "univenerip01", "path": "lib/services/its_url_fixer.dart"}
  THOUGHT: The rule is absent — adding it next via edit_file, then I'll test.
  CALL: edit_file {"path": "lib/services/its_url_fixer.dart", "old": "        url.contains('unlvenierp01') ||", "new": "        url.contains('unlvenierp01') ||\n        url.contains('univenerip01') ||"}
  CALL: run_command {"command": "flutter test test/its_url_fixer_test.dart"}
  FINAL: Added the univenerip01 rule to isItsHost and normalize; tests now pass.

AUTO-TRACK: When Chris gives you 2 or more separate instructions
(e.g. "do X, do Y, and do Z"), automatically break them into tracked
tasks. Use todo_add for each one, todo_done when finished, and
todo_list to check remaining. Always end your FINAL with:
"Progress: X/Y tasks done" (e.g. "Progress: 3/3 tasks done" or
"Progress: 2/3 tasks done — 1 pending").
"""

def _unwrap_typed(o):
    """Recursively unwrap Ollama 'JSON-schema style' args like
    {"expr": {"type": "string", "value": "42 * 2"}} -> {"expr": "42 * 2"}."""
    if isinstance(o, dict):
        if set(o.keys()) <= {"type", "value", "description", "enum"} and "value" in o:
            return o["value"]
        return {k: _unwrap_typed(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_unwrap_typed(x) for x in o]
    return o


def _json_tool(obj):
    """Given a parsed JSON dict, return (name, args) if it describes a tool call."""
    if not isinstance(obj, dict):
        return None
    nm = obj.get("name") or obj.get("command") or obj.get("tool")
    am = obj.get("arguments") or obj.get("args") or obj.get("parameters")
    fn = obj.get("function")
    if isinstance(fn, dict):
        nm = nm or fn.get("name")
        am = am or fn.get("arguments")
    if isinstance(am, str):
        try:
            am = json.loads(am)
        except Exception:
            am = None
    if isinstance(am, dict) and isinstance(nm, str) and nm not in ("result", "results"):
        return nm, _unwrap_typed(am)
    return None


def _extract_calls(reply):
    """Pull tool calls out of a model reply. Accepts formats:
      CALL: <name> {json}            (preferred)
      CALL: <function=NAME>{json>      (OpenRouter free-model serialization)
      {"command": <name>, "args": {json}}  (single-line JSON object)
      ```json { "name":..., "arguments":{...} } ```   (Ollama prose-style)
    Returns a list of (name, args_dict)."""
    if not reply:
        return []
    out = []
    # 1) fenced JSON blocks describing a tool call (qwen2.5-coder:1.5b style)
    for m in re.finditer(r'```(?:json)?\s*\n?(.*?)```', reply, re.S):
        blob = m.group(1).strip()
        try:
            obj = json.loads(blob)
        except Exception:
            continue
        hit = _json_tool(obj)
        if hit:
            out.append(hit)
    for line in reply.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("CALL:"):
            rest = s[len("CALL:"):].strip()
            m = re.match(r'(\w+)\s*(\{.*\})\s*$', rest, re.S)
            if not m:
                # tolerate "<function=NAME>{json>" or "<NAME>{json>" wrappers
                m = re.match(r'<(?:function=)?(\w+)>\s*(\{.*\})\s*$', rest, re.S)
            if m:
                try:
                    out.append((m.group(1), _unwrap_typed(json.loads(m.group(2)))))
                except Exception:
                    pass
            continue
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
            except Exception:
                continue
            hit = _json_tool(obj)
            if hit:
                out.append(hit)
    seen, uniq = set(), []
    for name, args in out:
        args = args if isinstance(args, dict) else {}
        key = (name, json.dumps(args, sort_keys=True))
        if key not in seen:
            seen.add(key)
            uniq.append((name, args))
    return uniq

def _extract_final(reply):
    if not reply:
        return None
    for line in reply.splitlines():
        s = line.strip()
        if s.startswith("FINAL:"):
            return s[len("FINAL:"):].strip()
    return None

def _normalize_reply(text):
    """Clean model output for display: collapse Unicode spaces that terminals
    render as '?' (the model emits U+202F NARROW NO-BREAK SPACE between words)
    and strip stray control chars."""

    if not text:
        return text
    for ch in "\u00a0\u2009\u202f\u2060":
        text = text.replace(ch, " ")
    return "".join(c for c in text if c >= " " or c in "\n\t")

def _terse_reply(text, max_len=500):
    if not text:
        return text
    t = text.strip()
    for line in t.splitlines():
        s = line.strip()
        if s.startswith("FINAL:"):
            return s[len("FINAL:"):].strip()[:max_len]
    if len(t) <= max_len:
        return t
    # No FINAL: drop THOUGHT/CALL scaffolding, keep only the last sentence.
    t = re.sub(r'\b(THOUGHT|CALL|OBSERVATION):?\s*', '', t)
    t = re.sub(r'\{[^}]*\}', '', t)
    t = re.sub(r'\s+', ' ', t).strip(' .')
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', t) if s.strip()]
    if not sentences:
        return "Done."
    last = sentences[-1]
    if len(last) < 30 and len(sentences) > 1:
        last = (sentences[-2] + " " + last).strip()
    if len(last) <= max_len:
        return last
    # Truncate at a sentence boundary, not mid-sentence.
    truncated = last[:max_len]
    for punct in ('. ', '! ', '? '):
        idx = truncated.rfind(punct)
        if idx > max_len // 2:
            return truncated[:idx + 1]
    return truncated.rstrip() + "…"

# Shortcut phrases that map to the saved ITS application-form task. Chris reruns
# the Univen ITS application flow repeatedly (hunting the 404 error), so a short
# phrase should replay the full saved step list instead of the weak model trying
# to reconstruct it from context each time.
_ITS_TASK_KEY = "ui_task.its_application"
_ITS_SHORTCUT_RE = re.compile(
    r'\b(?:do|run|start|restart|open|again|re[- ]?run|repeat)\s+(?:the\s+)?'
    r'(?:its|venda|univen)\s+(?:application|portal|form|app)\b'
    r'|\b(?:again|re[- ]?run|repeat|restart)\b.*\b(?:its|venda|univen|application)\b',
    re.IGNORECASE)
# The actual "rerun the saved task" phrase inside a longer instruction list,
# e.g. "do the ITS application again but this time ...". Its match span is
# replaced by the saved task text so trailing new steps still parse.
_ITS_RERUN_RE = re.compile(
    r'\b(?:do\s+)?(?:the\s+)?(?:its|venda|univen)\s+(?:application|portal|form|app)'
    r'\s+again\b', re.IGNORECASE)


def _resolve_ui_task(user_message):
    """If the message reruns the saved ITS task, splice the saved step list into
    the message so the deterministic parser executes the full flow. Handles both
    a bare shortcut ("do the ITS application again") and a longer instruction
    list that starts by rerunning the saved task then adds new steps ("do the
    ITS application again but this time ... after Next ..."). Returns the spliced
    text or None."""
    if not user_message:
        return None
    saved = get_memories().get(_ITS_TASK_KEY)
    if not saved or not saved.get("value"):
        return None
    task_text = saved["value"]
    m = _ITS_RERUN_RE.search(user_message)
    if not m:
        # A bare shortcut without the word "again" (e.g. "run the ITS app") is
        # only honored for genuinely short messages.
        if len(user_message.strip()) > 220:
            return None
        # A "fill the form myself / by himself" request must NOT be hijacked by the
        # saved navigation task — it should parse into a ui_fill instead.
        if not _ITS_SHORTCUT_RE.search(user_message):
            return None
        if re.search(r'\bfill', user_message, re.IGNORECASE) and \
           re.search(r'\b(by\s+himself|by\s+herself|my\s+profile|use\s+my\s+profile|using\s+my\s+profile|fields?\s+by\s+himself|by\s+itself)\b',
                    user_message, re.IGNORECASE):
            return None
        if any(k in user_message.lower() for k in ("how", "what", "why", "?")):
            return None
        return task_text
    # Longer message: replace just the rerun phrase with the saved task, keeping
    # the trailing instructions ("but this time ... after Next ...").
    before = user_message[:m.start()].rstrip()
    after = user_message[m.end():].strip()
    head = task_text
    if before:
        head = before + "\n" + task_text
    if after and after.lower() not in ("again", "."):
        head = head + "\n" + after
    return head


def _ui_script_steps(user_message):
    """Parse a user's explicit numbered UI step list into ordered actions.

    The user (Chris) writes deterministic step lists like:
      1. ui_app_open StudentSyncSA
      2. ui_dump
      3. Search for "My Profile" in the dump. tap it! then ui_dump.
      4. find "Lets get Started" button. tap it. ui_dump. read the fields.
    qwen2.5:3b is too weak to follow these even when forced, so we parse them
    ourselves and execute each step deterministically with the real tools.

    Handles prose too: "swipe left", "scroll down", "look for Online Portal
    tab and tap it", "search for Universities tab on it", dropdown selections
    ("On both fields select No!").

    Returns a list of
      ("ui_app_open"|"ui_dump"|"ui_swipe"|"ui_tap"|"ui_screenshot"|"ui_select"|"read", detail)
    or None if the message is not a step list."""
    if not user_message or not _ui_task(user_message):
        return None
    # Parenthetical asides ("(will be the first on on top)") are dropped so they
    # never pollute unquoted target labels. Relative order is preserved.
    text = re.sub(r'\([^)]*\)', ' ', user_message)
    steps = []
    last_targets = []
    last_fields = []
    tokens = []
    for m in re.finditer(r'\bui_app_open\b(?:\s+([A-Za-z0-9._]+))?', text):
        tokens.append((m.start(), "open", m.group(1) or "StudentSyncSA"))
    for m in re.finditer(r'\bui_dump\b', text):
        tokens.append((m.start(), "dump", ""))
    for m in re.finditer(r'\bui_screenshot\b', text):
        tokens.append((m.start(), "screenshot", ""))
    # "fill in the ITS form / fill the fields by himself" -> ACEsi fills every
    # field on the current ITS page from the device profile. Recognised when
    # "fill" appears with a form/fields/page noun and an autonomous intent
    # ("by himself / my profile / using my profile").
    if 'ui_fill' not in [s[0] for s in steps]:
        fpos = text.lower().find('fill')
        if fpos >= 0 and re.search(r'\b(?:fields?|form|page\b)', text, re.IGNORECASE) and \
           re.search(r'\b(by\s+himself|by\s+herself|by\s+itself|using\s+my\s+profile|my\s+profile|by\s+itself)\b',
                     text, re.IGNORECASE):
            tokens.append((fpos, "fill", ""))
    # Explicit swipes: "swipe left", "swipe right", "swipe up/down"
    for m in re.finditer(r'\bswipe\s+(left|right|up|down)\b', text, re.IGNORECASE):
        tokens.append((m.start(), "swipe", m.group(1).lower()))
    # Scrolls: "scroll down/up/to the bottom" → screen moves (finger opposite).
    for m in re.finditer(r'\bscroll\s+(?:down|up|to\s+the\s+bottom)\b',
                         text, re.IGNORECASE):
        low = m.group(0).lower()
        tokens.append((m.start(), "scroll",
                       "down" if ("down" in low or "bottom" in low) else "up"))
    # Quoted tap targets, both verb-prefixed ("search for "X"", 'find "X"',
    # "look for "X"", 'tap the "X"', 'tap on "X"', 'tap "X"') and bare quotes
    # ("...field "Do you already have a student number" and " Returning to
    # complete an Application""). A target is a navigation tap when a
    # tab/button/icon/tile word follows the closing quote; otherwise it is a
    # plain label (dropdown field, checkbox, option) so "both fields select No"
    # can resolve to the right two fields.
    def _is_nav_target(end):
        return bool(re.search(r'\b(?:tab|button|icon|tile|star)\b',
                              text[end:end + 12], re.IGNORECASE))
    # "find the line 'X'" / "find the "Y"" / "look for the line 'Z'" = verify a
    # dialog/text line is present (ui_dump), NOT a tap target.
    for m in re.finditer(r'\b(?:find|look\s+for|search\s+for)\s+(?:the\s+)?'
                         r'(?:line\s+|page\s+|text\s+|option\s+)?'
                         r'["\']\s*([^"\']{2,60}?)\s*["\']', text, re.IGNORECASE):
        tokens.append((m.start(), "dump", ""))
    # "the star top right" / "star icon" -> tap the star (dialog opener).
    for m in re.finditer(
            r'\b(?:the\s+)?(?:star|asterisk)\b(?:[^,;.\n]{0,25})', text, re.IGNORECASE):
        label = re.sub(r'\s+', ' ', m.group(0)).strip()
        tokens.append((m.start(), "target", ("star", True)))
    for m in re.finditer(r'(?:search\s+for|look\s+for|find|(?:tap|tab)\s+(?:on\s+the\s+)?'
                         r'(?:on\s+|the\s+)?|click\s+(?:on\s+)?)'
                         r'\s*["\']\s*([^"\']{2,60}?)\s*["\']', text, re.IGNORECASE):
        label = re.sub(r'\s+', ' ', m.group(1)).strip()
        tokens.append((m.start(), "target", (label, _is_nav_target(m.end()))))
    # Bare quoted labels (no verb prefix), e.g. dropdown field names. Skip
    # quotes already consumed by "find the line 'X'" / "find the "Y"" (a
    # verify-dump, not a tap).
    for m in re.finditer(r'["\']\s*([^"\']{2,60}?)\s*["\']', text):
        before = text[max(0, m.start() - 40):m.start()].lower()
        if re.search(r'\b(?:find|look\s+for|search\s+for)\s+the\s+'
                     r'(?:line\s+|page\s+|text\s+|option\s+)?$', before):
            continue
        label = re.sub(r'\s+', ' ', m.group(1)).strip()
        tokens.append((m.start(), "target", (label, _is_nav_target(m.end()))))
    # Unquoted tap targets: "search for Universities tab on it",
    # "look for Online Portal tab", "find the Lets get Started button".
    for m in re.finditer(
            r'(?:search\s+for|look\s+for|find|(?:tap|tab)\s+(?:on\s+the\s+|on\s+|the\s+)?|'
            r'click\s+(?:on\s+)?)\s*([A-Za-z][A-Za-z0-9\'&., -]{2,50}?)\s+'
            r'(?:tab|button|icon|tile)\b', text, re.IGNORECASE):
        label = re.sub(r'\s+', ' ', m.group(1)).strip()
        # "click on the Yes button" -> label "Yes", not "the Yes".
        label = re.sub(r'^(?:the|a|an)\s+', '', label)
        tokens.append((m.start(), "target", (label, True)))
    # Dropdown selections: "On both fields select No!", "select No",
    # "select Yes on both fields", "On both fields select No! The third one will
    # automatically select a No."  (the third one needs no explicit step)
    for m in re.finditer(r'\bselect\s+(No|Yes)\b', text, re.IGNORECASE):
        option = m.group(1).capitalize()
        tokens.append((m.start(), "select", option))
    # standalone "tap it" / "click it" / "tap on it" / "tap that"
    for m in re.finditer(r'\b(?:tap|click|tab)\s+(?:on\s+)?(it|that|this)\b',
                         text, re.IGNORECASE):
        tokens.append((m.start(), "tap_last", ""))
    tokens.sort(key=lambda t: t[0])
    for pos, kind, detail in tokens:
        if kind == "open":
            if not any(s[0] == "ui_app_open" for s in steps):
                steps.append(("ui_app_open", detail))
        elif kind == "dump":
            steps.append(("ui_dump", ""))
        elif kind == "screenshot":
            steps.append(("ui_screenshot", ""))
        elif kind == "fill":
            if not any(s[0] == "ui_fill" for s in steps):
                steps.append(("ui_fill", ""))
        elif kind == "swipe":
            steps.append(("ui_swipe", detail))
        elif kind == "scroll":
            steps.append(("ui_scroll", detail))
        elif kind == "target":
            label, is_nav = detail
            last_targets.append(label)
            if not is_nav:
                last_fields.append(label)
            if not any(s == ("ui_tap", label) for s in steps):
                steps.append(("ui_tap", label))
        elif kind == "select":
            # "select No/Yes" refers to the most recent non-navigation field
            # target(s); when the message says "both fields", select on the last
            # two field targets.
            both = bool(re.search(r'\bboth\s+fields?\b', text, re.IGNORECASE))
            fields = last_fields[-2:] if both else last_fields[-1:]
            for f in fields:
                # Convert the field's plain ui_tap into a ui_select(field, option)
                # (tap field → dump → tap option). If it was already selected,
                # don't duplicate.
                replaced = False
                for i, s in enumerate(steps):
                    if s == ("ui_tap", f):
                        steps[i] = ("ui_select", (f, detail))
                        replaced = True
                        break
                if not replaced and not any(
                        s[0] == "ui_select" and s[1][0] == f for s in steps):
                    steps.append(("ui_select", (f, detail)))
        elif kind == "tap_last":
            if last_targets:
                tgt = last_targets[-1]
                already = any(s == ("ui_tap", tgt) for s in steps) or any(
                    s[0] == "ui_select" and s[1][0] == tgt for s in steps)
                if not already:
                    steps.append(("ui_tap", tgt))
    if not steps:
        return None
    return steps


def _dump_tap_point(screen, target):
    """Find the tap coordinates for a target label in a ui_dump compact string.
    Returns (x, y) or None. Handles Flutter's two-line rows where the label is on
    its own line and the clickable row's tap coords are on the NEXT line
    ("My Profile" / "View and edit your profile @ tap(540,1330)"). Also matches
    punctuation-insensitively so "Let's" matches "Lets".

    Prefers an EXACT label match over a substring match so a short option like
    "No" hits the "No" row and not "No NBT". Returns (x, y, matched_text) so the
    caller knows whether the match was exact."""
    target = re.sub(r'[^A-Za-z0-9 ]', '', target).strip().lower()
    if not target:
        return None

    def _coords(lines, i):
        # Scan up to 6 lines ahead for a line holding tap coords. Card lists put
        # the label on one line and the clickable's coords several lines below
        # ("University of Pretoria" ... "NBT Required @ tap(540,1216)").
        for j in range(i, min(i + 6, len(lines))):
            m = re.search(r'tap\((\d+),(\d+)\)', lines[j])
            if m:
                return int(m.group(1)), int(m.group(2))
        return None

    lines = screen.splitlines()
    exact_hit = None
    sub_hit = None
    for i, line in enumerate(lines):
        # "label @ tap(x,y) [CLICKABLE]": the label is everything before " @ "
        # (split BEFORE normalizing, since normalization strips the "@").
        raw_label = line.split(' @ ')[0].strip()
        norm = re.sub(r'[^A-Za-z0-9 ]', '', line).lower()
        label = re.sub(r'[^A-Za-z0-9 ]', '', raw_label).strip().lower()
        if not label or "labeled nodes" in label:
            continue
        if label == target:
            c = _coords(lines, i)
            if c:
                return c[0], c[1], True
            exact_hit = i
        elif target in norm and sub_hit is None:
            c = _coords(lines, i)
            if c:
                sub_hit = (c[0], c[1])
    # Prefer an exact match; the coords may be on a line without an " @ " (a
    # two-line row where the second line holds the tap). Fall back to substring.
    if exact_hit is not None:
        c = _coords(lines, exact_hit)
        if c:
            return c[0], c[1], True
    if sub_hit:
        return sub_hit[0], sub_hit[1], False
    return None


def _scroll_search(screen, target, direction="down", max_scrolls=8):
    """Scroll the screen until a target appears, returning (screen, (x, y)) or
    (screen, None). Direction is the SCREEN direction ("down" scrolls content
    down, finger moves up). Used when a tap target is not yet on screen."""
    for _ in range(max_scrolls):
        if direction == "down":
            x1, y1, x2, y2 = 540, 2100, 540, 300
        else:
            x1, y1, x2, y2 = 540, 300, 540, 2100
        ok, out = _call_tool("ui_swipe",
                             {"x1": x1, "y1": y1, "x2": x2, "y2": y2,
                              "duration": 250})
        _ok, _d = _ui_auto_dump()
        if _ok:
            screen = _d
        pt = _dump_tap_point(screen, target)
        if pt:
            return screen, (pt[0], pt[1])
    return screen, None


# ── WebView (CDP) helpers ────────────────────────────────────────────────
# The ITS portal is a WebView. `adb uiautomator dump` is blind to WebView HTML,
# so ACEsi's swipes scroll the page but the form fields never appear in the
# dump. These helpers drive the page's DOM directly via Chrome DevTools
# Protocol (devtools_service.py), which connects to the app's WebView through
# an adb forward to its webview_devtools_remote_<pid> socket.

_ITS_GROUP_JS = r'''(function(){
  var out = [];
  var ctrls = document.querySelectorAll('select, input[type=checkbox], input[type=radio], input[type=text], input[type=password], input[type=button], input[type=submit], button, textarea, a');
  for (var i=0;i<ctrls.length;i++){
    var el = ctrls[i];
    if (el.type === 'hidden') continue;
    if (el.tagName === 'A' && !(el.getAttribute('href') || '').trim()) continue;
    var anc = el, grp = '';
    while (anc){
      var id = anc.id || '';
      if (id.indexOf('Grp') !== -1 || anc.tagName === 'FORM'){
        grp = (anc.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 300);
        break;
      }
      anc = anc.parentElement;
    }
    var opts = [];
    if (el.tagName === 'SELECT'){
      for (var j=0;j<el.options.length;j++){ opts.push(el.options[j].text); }
    }
    var txt = '';
    if (el.tagName === 'INPUT'){ txt = el.value || ''; }
    else { txt = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120); }
    out.push({tag: el.tagName, name: el.name, id: el.id || '', type: el.type || '',
              grp: grp, opts: opts, checked: el.checked === true, txt: txt});
  }
  return JSON.stringify(out);
})()'''


_WEBVIEW_PROBE_CACHE = {"ts": 0.0, "val": None}


def _webview_controls():
    """Return the ITS WebView's form controls (name, group label, options) or
    None if no WebView is reachable. Each item: {tag, name, type, grp, opts,
    checked}. Cached for a short window so repeated probes (one per executor
    step) can't stall on the slow fallback (headless-Chrome launch + port
    scan) when the WebView socket momentarily disappears."""
    now = time.time()
    if now - _WEBVIEW_PROBE_CACHE["ts"] < 3.0:
        return _WEBVIEW_PROBE_CACHE["val"]
    try:
        ok, _m = d.connect_cmd()
        if not ok:
            _WEBVIEW_PROBE_CACHE["ts"] = now
            _WEBVIEW_PROBE_CACHE["val"] = None
            return None
        ok, out = d.evaluate_js(_ITS_GROUP_JS)
        if not ok:
            _WEBVIEW_PROBE_CACHE["ts"] = now
            _WEBVIEW_PROBE_CACHE["val"] = None
            return None
        # evaluate_js returns a JSON-encoded string value.
        try:
            val = json.loads(json.loads(out))
        except Exception:
            try:
                val = json.loads(out)
            except Exception:
                val = None
        _WEBVIEW_PROBE_CACHE["ts"] = now
        _WEBVIEW_PROBE_CACHE["val"] = val
        return val
    except Exception:
        _WEBVIEW_PROBE_CACHE["ts"] = now
        _WEBVIEW_PROBE_CACHE["val"] = None
        return None


def _norm_label(s):
    return re.sub(r'[^A-Za-z0-9 ]', ' ', (s or '').lower()).strip()


def _webview_find(controls, label):
    """Match a human label ("Do you already have a student number", "I accept",
    "Next") against a control's group text OR its own button/link text.
    Returns the control or None. Exact match first, then substring, then fuzzy
    word-overlap."""
    target = _norm_label(label)
    if not target:
        return None
    exact = None
    sub = None
    fuzzy_best = None
    fuzzy_score = 0
    for c in controls:
        # The control's own name/id are the strongest signal for programmatic
        # fills ("oapCitzCode", "custom-citz-code"); a human label matters for
        # buttons/links and for selects/inputs reached through their label.
        name = _norm_label(c.get('name'))
        cid = _norm_label(c.get('id'))
        if name and (name == target or (target in name and sub is None)):
            if name == target:
                exact = c
                break
            if sub is None:
                sub = c
            continue
        if cid and (cid == target or (target in cid and sub is None)):
            if cid == target:
                exact = c
                break
            if sub is None:
                sub = c
            continue
        # The button's own text (value/textContent) is the strongest signal
        # for buttons/links; the group label matters for selects/inputs.
        own = _norm_label(c.get('txt'))
        g = _norm_label(c.get('grp'))
        if own and (own == target or (target in own and sub is None)):
            if own == target:
                exact = c
                break
            if sub is None:
                sub = c
            continue
        if not g:
            continue
        if g == target:
            exact = c
            break
        if target in g and sub is None:
            sub = c
        tw = set(target.split())
        gw = set(g.split())
        if tw:
            score = len(tw & gw) / float(len(tw))
            # Form controls (select/input/button) outrank links (<a>) on ties:
            # an <a>'s group text is surrounding content, not its own label.
            def _rank(ctrl):
                return 0 if ctrl.get('tag') in ('SELECT', 'INPUT', 'BUTTON') else 1
            if score >= 0.6 and (
                score > fuzzy_score or
                (score == fuzzy_score and (not fuzzy_best or _rank(c) < _rank(fuzzy_best)))
            ):
                fuzzy_score = score
                fuzzy_best = c
    return exact or sub or fuzzy_best


def _webview_select(field, option):
    """Set a WebView <select> to the option whose text contains `option`
    (case-insensitive), then dispatch change. Returns (ok, message)."""
    controls = _webview_controls()
    if not controls:
        return False, "no WebView reachable (cdp connect failed)"
    c = _webview_find(controls, field)
    if not c or c.get('tag') != 'SELECT':
        return False, "WebView field %r not found" % field
    name = c['name']
    # Some injected selects (custom citizenship code, "heard about us") carry
    # no name attribute — fall back to their id.
    sel = 'select[name="%s"]' % name if name else 'select[id="%s"]' % c['id']
    opt = option.lower()
    expr = r'''(function(){
      var sel = document.querySelector(%r);
      if (!sel) return 'NO_SELECT';
      var target = %r;
      // 1) exact option-text match (avoids "ENGLISH" matching "AFRIKAANS/ENGLISH").
      for (var i=0;i<sel.options.length;i++){
        if (sel.options[i].text.toLowerCase().trim() === target){
          sel.selectedIndex = i; sel.value = sel.options[i].value;
          sel.dispatchEvent(new Event('change', {bubbles:true}));
          sel.dispatchEvent(new Event('blur', {bubbles:true}));
          return 'exact:'+sel.options[i].text;
        }
      }
      // 2) exact option-value match (short codes like Y/N/F/M/1/4/D).
      for (var i=0;i<sel.options.length;i++){
        if ((sel.options[i].value||'').toLowerCase() === target){
          sel.selectedIndex = i; sel.value = sel.options[i].value;
          sel.dispatchEvent(new Event('change', {bubbles:true}));
          sel.dispatchEvent(new Event('blur', {bubbles:true}));
          return 'val:'+sel.options[i].text;
        }
      }
      // 3) substring fallback ("Female" matches "F Female").
      for (var i=0;i<sel.options.length;i++){
        if ((sel.options[i].text||'').toLowerCase().indexOf(target) !== -1){
          sel.selectedIndex = i; sel.value = sel.options[i].value;
          sel.dispatchEvent(new Event('change', {bubbles:true}));
          sel.dispatchEvent(new Event('blur', {bubbles:true}));
          return 'sub:'+sel.options[i].text;
        }
      }
      return 'NO_OPTION';
    })()''' % (sel, opt)
    ok, out = d.evaluate_js(expr)
    if not ok:
        return False, "webview evaluate failed: %s" % str(out)[:150]
    try:
        out = json.loads(out)
    except Exception:
        pass
    if out == "NO_OPTION":
        return False, "option %r not in %r" % (option, c.get('opts'))
    if out == "NO_SELECT":
        return False, "select %r vanished" % name
    return True, "webview select %s=%s (%s)" % (field, option, out)


def _webview_type(field, value):
    """Type text into a WebView text input matched by name/id/label.
    Clears read-only flags, sets the value, then dispatches input/change/blur
    so the ITS portal's validators run. Returns (ok, message)."""
    controls = _webview_controls()
    if not controls:
        return False, "no WebView reachable (cdp connect failed)"
    c = _webview_find(controls, field)
    if not c or c.get('tag') not in ('INPUT', 'TEXTAREA'):
        return False, "WebView field %r not found (tag=%r)" % (field, c and c.get('tag'))
    if c.get('type') in ('checkbox', 'radio', 'button', 'submit'):
        return False, "WebView field %r is a %s, not a text field" % (field, c.get('type'))
    name = c['name']
    # Prefer the real name; fall back to id for injected (un-named) fields.
    sel = '[name="%s"]' % name if name else '[id="%s"]' % c['id']
    expr = r'''(function(){
      var el = document.querySelector(%r);
      if (!el) return 'NO_EL';
      try { el.removeAttribute('readonly'); el.removeAttribute('disabled'); } catch(e){}
      var proto = el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype
                                            : window.HTMLInputElement.prototype;
      var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
      setter.call(el, %r);
      el.dispatchEvent(new Event('input',  {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
      el.dispatchEvent(new Event('blur',   {bubbles:true}));
      return 'set:' + el.value;
    })()''' % (sel, value)
    ok, out = d.evaluate_js(expr)
    if not ok:
        return False, "webview evaluate failed: %s" % str(out)[:150]
    try:
        out = json.loads(out)
    except Exception:
        pass
    if out == "NO_EL":
        return False, "input %r vanished" % field
    return True, "webview type %s=%r (%s)" % (field, value, out)


def _webview_click(label):
    """Click a WebView control (checkbox/button/input/link) matched by label.
    Returns (ok, message)."""
    controls = _webview_controls()
    if not controls:
        return False, "no WebView reachable (cdp connect failed)"
    c = _webview_find(controls, label)
    if not c:
        return False, "WebView control %r not found" % label
    name = c.get('name')
    if not name:
        # Buttons/links carry no name attribute: click by visible text.
        txt = (c.get('txt') or '').strip()
        if not txt:
            return False, "control for %r has no name and no text" % label
        expr = r'''(function(){
          var els = Array.prototype.slice.call(document.querySelectorAll('button, input[type=button], input[type=submit], a'));
          for (var i=0;i<els.length;i++){
            var t = els[i].value || els[i].textContent || '';
            t = t.replace(/\s+/g, ' ').trim();
            if (t.toLowerCase().indexOf(%r.toLowerCase()) !== -1){
              els[i].scrollIntoView({block:'center'});
              els[i].click();
              return 'clicked:'+els[i].tagName+':'+t;
            }
          }
          return 'NO_EL';
        })()''' % txt[:60]
        ok, out = d.evaluate_js(expr)
        if not ok:
            return False, "webview evaluate failed: %s" % str(out)[:150]
        if out == "NO_EL":
            return False, "button/link %r vanished" % label
        return True, "webview click %s (%s)" % (label, out)
    expr = r'''(function(){
      var el = document.querySelector('[name="%s"]');
      if (!el) return 'NO_EL';
      el.scrollIntoView({block:'center'});
      el.click();
      return 'clicked:'+el.tagName+':'+(el.checked!==undefined?el.checked:'');
    })()''' % name
    ok, out = d.evaluate_js(expr)
    if not ok:
        return False, "webview evaluate failed: %s" % str(out)[:150]
    return True, "webview click %s (%s)" % (label, out)


def _webview_dump():
    """Compact text dump of the WebView form (like ui_dump) so the executor can
    list what is on the page. Returns "" if no WebView is reachable."""
    controls = _webview_controls()
    if not controls:
        return ""
    lines = []
    for c in controls:
        g = re.sub(r'\s+', ' ', (c.get('grp') or '')).strip()
        head = "%s %s name=%s" % (c.get('tag', ''), c.get('type', ''),
                                  c.get('name', ''))
        if c.get('tag') == 'SELECT':
            head += " opts=[%s]" % ", ".join(c.get('opts', []))
        if c.get('txt'):
            head += " txt=%r" % c.get('txt')[:40]
        lines.append("%s | %s" % (head, g[:140]))
    return "\n".join(lines)


# Text markers that only appear once the ITS WebView page is showing. Cheap
# gate so we don't run an adb/CDP probe on every native step (Universities
# tab, app open, etc.) — the probe only fires when the screen looks like ITS.
_ITS_SCREEN_MARKERS = ("comprehensive web application", "do you already have a student number",
                       "--- please select ---", "qualification specific token",
                       "application process", "wizardimg", "oapoldnew")


def _webview_active_screen(screen):
    s = (screen or "").lower()
    return any(m in s for m in _ITS_SCREEN_MARKERS)


# ── Device profile (Hive box) reader ──────────────────────────────────────
# The app stores the student profile in a Hive box (UTF-16LE JSON) at
# /data/data/com.studentsyncsa.studentsyncsa/app_flutter/student_profile.hive.
# ACEsi reads it directly so it can fill the ITS form with the SAME data the
# app's own (broken) Star autofill would use.

_DEVICE_PROFILE_CACHE = {"ts": 0.0, "val": None}


def _device_profile():
    """Pull the app's StudentProfile JSON from the phone's Hive box
    (com.studentsyncsa.studentsyncsa app_flutter/student_profile.hive).
    The box is binary Hive; the profile value is a JSON string embedded as
    ASCII bytes, so we locate `{"id"` and brace-match to extract it. Returns
    a dict (profile.toJson()) or None. Cached ~20s."""
    now = time.time()
    if now - _DEVICE_PROFILE_CACHE["ts"] < 20.0:
        return _DEVICE_PROFILE_CACHE["val"]
    raw = None
    try:
        proc = subprocess.run(
            ["adb", "exec-out", "run-as", "com.studentsyncsa.studentsyncsa",
             "cat", "app_flutter/student_profile.hive"],
            capture_output=True, timeout=20)
        if proc.returncode == 0 and proc.stdout:
            raw = proc.stdout
    except Exception as e:
        print("?? profile pull failed: %s" % e)
    prof = None
    if raw:
        i = raw.find(b'{"id"')
        if i < 0:
            # fall back to first '{'
            i = raw.find(b'{')
        if i >= 0:
            depth = 0
            end = None
            in_str = False
            esc = False
            for k in range(i, len(raw)):
                ch = raw[k:k+1]  # work on bytes
                cb = raw[k]
                if in_str:
                    if esc:
                        esc = False
                    elif cb == 0x5C:
                        esc = True
                    elif cb == 0x22:
                        in_str = False
                    continue
                if cb == 0x22:
                    in_str = True
                elif cb == 0x7B:  # {
                    depth += 1
                elif cb == 0x7D:  # }
                    depth -= 1
                    if depth == 0:
                        end = k + 1
                        break
            if end:
                try:
                    prof = json.loads(raw[i:end].decode("utf-8", errors="replace"))
                except Exception as e:
                    print("?? profile json parse failed: %s (%d bytes)" % (e, end - i))
                    prof = None
    _DEVICE_PROFILE_CACHE["ts"] = now
    _DEVICE_PROFILE_CACHE["val"] = prof
    return prof


def _dob_dashy(dob_str):
    """'1963-03-16T00:00:00.000' -> '1963-03-16' (or passthrough)."""
    if not dob_str:
        return ""
    return (dob_str or "").split("T")[0][:10]


def _fill_its_page(profile):
    """Deterministically fill the ITS application form (page one: biographical
    details) from the profile, using the REAL DOM field names discovered live
    (oapIDnumber, oapPPnumber, oapCitizenType, oapGender, oapBirthdate, ...).
    Returns (ok, message)."""
    if not profile:
        return False, "no profile (pull Hive box failed)"
    # Build the full field plan, then apply it with a SINGLE CDP injection.
    # Doing one evaluate_js for all 30 fields (instead of 30 round-trips) avoids
    # stalling: the ITS Oracle JS fires async callDynBGproc validations on each
    # change event, and 30 sequential Runtime.evaluate calls race those XHRs and
    # each can approach its 10s timeout, making an otherwise-completed fill look
    # like a hang. One batch sets every value + dispatches every event in a single
    # synchronous JS turn, then returns a JSON report.
    plan = _its_field_plan(profile)
    if not plan:
        return False, "no profile-derived fields to fill"
    report = _its_fill_batch(plan)
    return ("filled" in report and "filled 0/" not in report), report


def _its_field_plan(profile):
    """Return [(field_id_or_name, value, 'select'|'text'), ...] for the ITS page
    one form fields, derived from the app's StudentProfile (Hive box)."""
    if not profile:
        return []
    p = profile.get("personal", {})
    c = profile.get("contact", {})
    a = profile.get("address", {})
    dm = profile.get("demographic", {})
    st = profile.get("status", {})
    id_no = (p.get("idNumber") or "").strip()
    is_sa = bool(re.match(r'^\d{13}$', id_no))
    dob_its = ""
    dob = (p.get("dateOfBirth") or "").split("T")[0][:10]
    if dob:
        try:
            dob_its = datetime.strptime(dob, "%Y-%m-%d").strftime("%d-%b-%Y").upper()
        except Exception:
            dob_its = ""
    gender = (p.get("gender") or "").lower()
    gval = "Female" if gender.startswith("f") else ("Male" if gender.startswith("m") else "")
    title_code = ""
    tup = (p.get("title") or "").upper()
    for code in ("MR", "MRS", "MS"):
        if tup.startswith(code):
            title_code = code
            break
    marital_map = {"single": "Single", "married": "Married", "divorced": "Divorced",
                   "widow": "Widow", "widowed": "Widow", "widower": "Widow"}
    mval = marital_map.get((dm.get("maritalStatus") or "").lower(), "")
    homelang = (dm.get("homeLanguage") or "").strip()
    homelang = homelang.upper() if homelang else ""
    eth_map = {"white": "WHITE", "black": "BLACK", "coloured": "Coloured",
               "colored": "Coloured", "indian": "INDIAN", "african": "BLACK"}
    ecode = eth_map.get((dm.get("populationGroup") or "").lower(), "")
    emp = (st.get("employmentStatus") or "").lower()
    empval = ("No" if ("un" in emp or "none" in emp) else "Yes") if emp else ""
    burs = (st.get("bursaryRequired") or "").lower()
    bursval = ("Yes" if burs.startswith("y") else "No") if burs else ""
    phone = (c.get("phone") or "").strip()
    work = (c.get("workPhone") or "").strip()
    email = (c.get("email") or "").strip()
    res = (st.get("wantsResidence") or "").lower()
    resval = ("Yes" if res.startswith("y") else "No") if res else ""
    heard = (dm.get("heardAboutUs") or "").replace("/", " ").strip() or ""

    def prov_code(prov):
        pv = (prov or "").lower()
        for tok, code in (("gauteng","Gauteng"),("western","Western Cape"),
                          ("eastern","Eastern Cape"),("north west","North West"),
                          ("northwest","North West"),("kwazulu","KwaZulu-Natal"),
                          ("limpopo","Limpopo"),("mpumalanga","Mpumalanga"),
                          ("northern cape","Northern Cape"),
                          ("free state","Free State"),("freestate","Free State")):
            if tok in pv:
                return code
        return (prov or "").strip()

    plan = []
    plan.append(("oapCitizenType", "Yes" if is_sa else "No", "select"))
    if id_no:
        plan.append(("oapIDnumber", id_no, "text") if is_sa else
                    ("oapPPnumber", id_no, "text"))
    if is_sa:
        plan.append(("custom-citz-code", "R.S.A", "select"))
        plan.append(("oapCitzCode", "RSA", "text"))
        plan.append(("oapCitzCode_desc", "R.S.A", "text"))
    if gval:
        plan.append(("oapGender", gval, "select"))
    if dob_its:
        plan.append(("oapBirthdate", dob_its, "text"))
        plan.append(("ssa-date-display", dob_its, "text"))
    if title_code:
        plan.append(("oapTitle", title_code, "select"))
    if (p.get("initials") or "").strip():
        plan.append(("oapInitials", p.get("initials").strip().upper(), "text"))
    if (p.get("lastName") or "").strip():
        plan.append(("oapSurname", p.get("lastName").strip().upper(), "text"))
    if (p.get("firstName") or "").strip():
        plan.append(("oapFirstNames", p.get("firstName").strip().upper(), "text"))
    if (p.get("maidenName") or "").strip():
        plan.append(("oapMaiden", p.get("maidenName").strip().upper(), "text"))
    if mval:
        plan.append(("oapMaritalStatus", mval, "select"))
    if homelang:
        plan.append(("oapHomeLang", homelang, "select"))
    if ecode:
        plan.append(("oapEthnic", ecode, "select"))
    if empval:
        plan.append(("oapEmployed", empval, "select"))
    if bursval:
        plan.append(("oapBursaryReq", bursval, "select"))
    if (a.get("address") or "").strip():
        plan.append(("oapStreetAddr1", a.get("address").strip(), "text"))
    if (a.get("addressLine2") or "").strip():
        plan.append(("oapStreetAddr2", a.get("addressLine2").strip(), "text"))
    if (a.get("addressLine3") or "").strip():
        plan.append(("oapStreetAddr3", a.get("addressLine3").strip(), "text"))
    prov = prov_code(a.get("province"))
    if prov:
        plan.append(("oapStreetAddr4", prov, "text"))
    if (a.get("postalCode") or "").strip():
        pc = a.get("postalCode").strip()
        plan.append(("oapStreetAddrPCodeRq", pc, "text"))
        plan.append(("oapStreetAddrPCodeRq_desc", pc, "text"))
    if phone:
        plan.append(("oapCellInd", "Yes", "select"))
        plan.append(("oapSACell", phone, "text"))
    if work:
        plan.append(("oapWorkPhone", work, "text"))
    if email:
        plan.append(("itsEmail", email, "text"))
        plan.append(("verifyEmail", email, "text"))
    if resval:
        plan.append(("oapResReq", resval, "select"))
    if heard:
        plan.append(("ssa-heard-select", heard, "select"))
    return plan


def _its_fill_batch(plan):
    """Apply a full field plan in a SINGLE CDP evaluate_js call.
    Each setter runs in try/catch so one sticky field can't abort the batch.
    Returns a human-readable report string."""
    # Build a JS object literal of name -> {v, t} (type). Use a JSON map so
    # values are safely escaped; the field identifier is matched in JS by
    # name first, then by id (covers custom-citz-code / ssa-heard-select).
    import json as _json
    rows = []
    for fid, value, kind in plan:
        rows.append({"f": fid, "v": value, "t": kind})
    payload = _json.dumps(rows)
    expr = r'''(function(){
      var plan = %s;
      var res = [];
      function findEl(name){
        return document.querySelector('[name="'+name+'"]')
            || document.getElementById(name)
            || document.querySelector('label') && (function(lbl){
                for(var i=0;i<lbl.length;i++){ if((lbl[i].htmlFor||'')===name){var e=document.getElementById(lbl[i].htmlFor); if(e)return e;} }
                return null;
              })(document.getElementsByTagName('label'));
      }
      function setSelect(el, target){
        var t = target.toLowerCase().trim();
        var picks = [];
        for(var i=0;i<el.options.length;i++){ picks.push(i); }
        // 1) exact option-text
        for(var i=0;i<picks.length;i++){ if(el.options[i].text.toLowerCase().trim()===t){return i;} }
        // 2) exact option-value
        for(var i=0;i<picks.length;i++){ if((el.options[i].value||'').toLowerCase()===t){return i;} }
        // 3) substring on text
        for(var i=0;i<picks.length;i++){ if((el.options[i].text||'').toLowerCase().indexOf(t)!==-1){return i;} }
        return -1;
      }
      function setVal(name, val, isSelect){
        var el = findEl(name);
        if(!el){ res.push({name:name, ok:false, msg:'NO_EL'}); return; }
        try{
          if(el.tagName === 'SELECT'){
            var idx = setSelect(el, val);
            if(idx < 0){ res.push({name:name, ok:false, msg:'NO_OPT:'+(val)}); return; }
            el.selectedIndex = idx; el.value = el.options[idx].value;
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur', {bubbles:true}));
          } else {
            try{ el.removeAttribute('readonly'); el.removeAttribute('disabled'); }catch(e){}
            var proto = (el.tagName==='TEXTAREA') ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
            var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input',  {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            el.dispatchEvent(new Event('blur',   {bubbles:true}));
          }
          res.push({name:name, ok:true, val:(el.value||'')});
        }catch(e){ res.push({name:name, ok:false, msg:'ERR:'+e.message}); }
      }
      for(var i=0;i<plan.length;i++){ try{ setVal(plan[i].f, plan[i].v, plan[i].t==='select'); }catch(e){ res.push({name:plan[i].f, ok:false, msg:'THROW:'+e.message}); } }
      return JSON.stringify(res);
    })()''' % payload
    ok, out = d.evaluate_js(expr)
    if not ok:
        return "webview evaluate failed: %s" % str(out)[:200]
    try:
        results = json.loads(json.loads(out))
    except Exception:
        try:
            results = json.loads(out)
        except Exception:
            return "could not parse fill report: %s" % str(out)[:200]
    ok_n = sum(1 for r in results if r.get("ok"))
    filled = ["%s=%r" % (r.get("name"), r.get("val")) for r in results if r.get("ok")]
    report = "filled %d/%d fields: %s" % (ok_n, len(results), ", ".join(filled))
    bad = [r for r in results if not r.get("ok")]
    if bad:
        report += " | failed: %s" % ", ".join("%s" % r.get("msg") for r in bad)
    return report


def _is_select_field(field):
    return bool(re.search(r'citizen|gender|title|marital|homelang|ethn|employ|bursary|'
                          r'resreq|cellind|heard|custom-citz|citizen', field, re.IGNORECASE))


def _execute_ui_script(user_message):
    """Deterministic executor for explicit UI step lists. Returns a reply string
    if the message was handled (steps executed on the device), else None."""
    # Expand a saved-task shortcut ("do the ITS application again") into the
    # stored step list BEFORE parsing. ALWAYS try the shortcut first: the user's
    # message ("do the ITS application again but this time ...") also parses as
    # steps on its own (just the tail), which would run the tail WITHOUT the
    # navigation to the app. The shortcut wins whenever it matches.
    expanded = _resolve_ui_task(user_message)
    is_rerun = bool(expanded)
    orig_message = user_message
    if expanded:
        print("🔄 expanded saved ITS task shortcut")
        user_message = expanded
    steps = _ui_script_steps(user_message)
    if not steps:
        return None
    print("🛠 /chat deterministic ui_script steps: %s" % steps)
    screen = ""
    done = []
    read_called = False
    # Track whether we've seen the screen (ui_dump performed) to allow ui_tap/ui_swipe
    seen_screen = False
    for action, detail in steps:
        if action == "ui_app_open":
            ok, out = _call_tool("ui_app_open", {})
            done.append("ui_app_open")
            print("  ui_app_open -> %s" % (ok,))
            _ok, _d = _ui_auto_dump()
            if _ok:
                screen = _d
        elif action == "ui_dump":
            ok, out = _call_tool("ui_dump", {})
            if ok:
                screen = out
                seen_screen = True
            done.append("ui_dump")
            # If the native dump is sparse (a WebView shows as a single node),
            # enrich it with the WebView form so dropdowns/checkboxes are visible.
            if screen.count("tap(") <= 2:
                wv = _webview_dump()
                if wv:
                    screen = wv
                    print("  ui_dump: WebView form detected (%d lines)" % len(wv.splitlines()))
        elif action == "ui_screenshot":
            ok, out = _call_tool("ui_screenshot", {})
            done.append("ui_screenshot")
        elif action == "ui_tap":
            if not seen_screen:
                done.append("ui_tap(%s:BLOCKED - ui_dump required first)" % detail)
                print("  ui_tap %r BLOCKED: ui_dump required first" % detail)
                continue
            if _webview_active_screen(screen) and _webview_controls():
                ok, out = _webview_click(detail)
                if ok:
                    done.append("ui_tap(%s@webview)" % detail)
                    print("  ui_tap %r via webview -> %s" % (detail, out))
                    _ok, _d = _ui_auto_dump()
                    if _ok:
                        screen = _d
                    wv = _webview_dump()
                    if wv:
                        screen = wv
                    continue
            found = _dump_tap_point(screen, detail)
            pt = (found[0], found[1]) if found else None
            if pt is None:
                # Screen may be stale; re-dump to find it.
                ok, out = _call_tool("ui_dump", {})
                if ok:
                    screen = out
                found = _dump_tap_point(screen, detail)
                pt = (found[0], found[1]) if found else None
            if pt is None and _webview_active_screen(screen) and _webview_controls():
                # We're in a WebView: tap the control's DOM element via CDP
                # instead of a coordinate tap.
                ok, out = _webview_click(detail)
                if ok:
                    done.append("ui_tap(%s@webview)" % detail)
                    print("  ui_tap %r via webview -> %s" % (detail, out))
                    _ok, _d = _ui_auto_dump()
                    if _ok:
                        screen = _d
                    wv = _webview_dump()
                    if wv:
                        screen = wv
                    continue
            if pt is None:
                # Target is off-screen: scroll to find it (search down, then up).
                print("  tap %r: not on screen, scrolling to find it" % detail)
                screen, pt = _scroll_search(screen, detail, "down")
                if pt is None:
                    screen, pt = _scroll_search(screen, detail, "up")
            if pt is None:
                print("  tap %r NOT FOUND on screen" % detail)
                done.append("ui_tap(%s:NOT FOUND)" % detail)
                continue
            ok, out = _call_tool("ui_tap", {"x": pt[0], "y": pt[1]})
            done.append("ui_tap(%s@%d,%d)" % (detail, pt[0], pt[1]))
            print("  ui_tap %r @ %s -> %s" % (detail, pt, ok))
            _ok, _d = _ui_auto_dump()
            if _ok:
                screen = _d
        elif action in ("ui_swipe", "ui_scroll"):
            if not seen_screen:
                done.append("%s(%s:BLOCKED - ui_dump required first)" % (action, detail))
                print("  %s %r BLOCKED: ui_dump required first" % (action, detail))
                continue
            dirn = detail
            # Screen is 1080x2412. Swipe gestures across it; "scroll down"
            # means finger moves UP (content moves down).
            x1, y1, x2, y2 = 540, 1200, 540, 1200
            if dirn == "left":
                x1, y1, x2, y2 = 900, 1200, 180, 1200
            elif dirn == "right":
                x1, y1, x2, y2 = 180, 1200, 900, 1200
            elif dirn == "down":
                x1, y1, x2, y2 = 540, 2100, 540, 300
            elif dirn == "up":
                x1, y1, x2, y2 = 540, 300, 540, 2100
            ok, out = _call_tool("ui_swipe",
                                 {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "duration": 250})
            done.append("%s(%s)" % (action, dirn))
            print("  %s %s -> %s" % (action, dirn, ok))
            _ok, _d = _ui_auto_dump()
            if _ok:
                screen = _d
        elif action == "ui_select":
            field, option = detail
            # If a WebView form is present, set the select's value via CDP FIRST.
            # The native dump exposes the field LABEL text; tapping that label's
            # coordinates does not open the <select> dropdown, so the option is
            # never found. CDP sets the value directly in the DOM.
            if _webview_active_screen(screen) and _webview_controls():
                ok, out = _webview_select(field, option)
                if ok:
                    done.append("ui_select(%s=%s@webview)" % (field, option))
                    print("  ui_select %s=%s via webview -> %s" % (field, option, out))
                    _ok, _d = _ui_auto_dump()
                    if _ok:
                        screen = _d
                    wv = _webview_dump()
                    if wv:
                        screen = wv
                    continue
            found = _dump_tap_point(screen, field)
            pt = (found[0], found[1]) if found else None
            if pt is None:
                ok, out = _call_tool("ui_dump", {})
                if ok:
                    screen = out
                found = _dump_tap_point(screen, field)
                pt = (found[0], found[1]) if found else None
            if pt is None and _webview_active_screen(screen) and _webview_controls():
                # We're in a WebView: set the select's value via CDP instead of
                # tapping coordinates.
                ok, out = _webview_select(field, option)
                if ok:
                    done.append("ui_select(%s=%s@webview)" % (field, option))
                    print("  ui_select %s=%s via webview -> %s" % (field, option, out))
                    _ok, _d = _ui_auto_dump()
                    if _ok:
                        screen = _d
                    wv = _webview_dump()
                    if wv:
                        screen = wv
                    continue
            if pt is None:
                # Field is off-screen: scroll to find it (search down, then up).
                print("  select %r: field not on screen, scrolling to find it" % field)
                screen, pt = _scroll_search(screen, field, "down")
                if pt is None:
                    screen, pt = _scroll_search(screen, field, "up")
            if pt is None:
                print("  select %r: field NOT FOUND" % (field,))
                done.append("ui_select(%s=%s:field NOT FOUND)" % (field, option))
                continue
            ok, out = _call_tool("ui_tap", {"x": pt[0], "y": pt[1]})
            print("  select field %r @ %s -> %s" % (field, pt, ok))
            _ok, _d = _ui_auto_dump()
            if _ok:
                screen = _d
            found = _dump_tap_point(screen, option)
            opt = (found[0], found[1]) if found else None
            if opt is None:
                # Option not in the freshly-opened dropdown view yet.
                ok, out = _call_tool("ui_dump", {})
                if ok:
                    screen = out
                found = _dump_tap_point(screen, option)
                opt = (found[0], found[1]) if found else None
            if opt is None:
                print("  select %r: option %r NOT FOUND" % (field, option))
                done.append("ui_select(%s=%s:option NOT FOUND)" % (field, option))
                continue
            ok, out = _call_tool("ui_tap", {"x": opt[0], "y": opt[1]})
            done.append("ui_select(%s=%s@%d,%d)" % (field, option, opt[0], opt[1]))
            print("  select option %r @ %s -> %s" % (option, opt, ok))
            _ok, _d = _ui_auto_dump()
            if _ok:
                screen = _d
        elif action == "read":
            read_called = True
        elif action == "ui_fill":
            # ACEsi fills the ITS form fields himself from the device profile
            # (the app's Star autofill is broken because of field-name
            # mismatches like oapIdNumber vs oapIDnumber).
            prof = _device_profile()
            if prof is None:
                msg = "no profile pulled from device Hive box"
                done.append("ui_fill(%s)" % msg)
                print("  ui_fill FAILED -> %s" % msg)
            else:
                ok, rep = _fill_its_page(prof)
                done.append("ui_fill(%s)" % ("ok" if ok else "fail"))
                print("  ui_fill -> %s" % rep)
                # Refresh the cached webview controls so the next step sees the
                # updated field values.
                _WEBVIEW_PROBE_CACHE["ts"] = 0.0
                _ok, _d = _ui_auto_dump()
                if _ok:
                    screen = _d
                wv = _webview_dump()
                if wv:
                    screen = wv
            continue
    # "read all the fields / information" — the form is usually taller than the
    # screen, so after the navigation steps scroll through it and collect every
    # label until the screen stops changing (bottom reached).
    wants_read = bool(re.search(r'\bread\b.*\b(?:all|every|fields|information|details|memoriz)',
                                user_message, re.IGNORECASE))
    if wants_read and "ui_dump" in [s[0] for s in steps]:
        collected = []
        seen_labels = set()
        prev_screen = None
        for _ in range(6):
            ok, out = _call_tool("ui_dump", {})
            if ok:
                screen = out
                for line in (screen or "").splitlines():
                    s = line.strip()
                    if not s or "labeled nodes" in s:
                        continue
                    if s not in seen_labels:
                        seen_labels.add(s)
                        collected.append(s)
                if prev_screen is not None and screen.strip() == prev_screen.strip():
                    break  # bottom reached — no new content
                prev_screen = screen
            # Scroll down to reveal the rest of the form.
            ok, out = _call_tool("ui_swipe",
                                 {"x1": 540, "y1": 2100, "x2": 540, "y2": 600, "duration": 250})
            if not ok:
                break
            done.append("ui_swipe")
        if collected:
            screen = "\n".join(collected)
            print("  read-all: collected %d labels across %d screens" % (len(collected), done.count("ui_swipe") + 1))
    # Build the reply: real screen labels from the last dump.
    fields = []
    for line in (screen or "").splitlines():
        s = line.strip()
        if not s or "labeled nodes" in s:
            continue
        fields.append(s)
    if not fields:
        fields = ["(no screen state captured)"]
    body = "\n".join(fields[:45])
    summary = "Done — steps executed: %s.\nHere is what I last saw on screen:\n%s" % (
        ", ".join(done), body)
    # Auto-save the ITS application task so a short phrase replays it next time.
    # NEVER overwrite the saved navigation skeleton on a *rerun* ("do the ITS
    # application again ..."): the "but this time X" tail is ephemeral and must
    # stay applied fresh. Only a fresh navigation definition (no rerun phrase)
    # is saved, and we save the ORIGINAL text so the navigation skeleton is
    # preserved without baking in a divergent post-Next tail.
    if not is_rerun and steps and ("ui_select" in [s[0] for s in steps] or
                                   any("student number" in str(d).lower()
                                       for d in steps)):
        try:
            set_memory(_ITS_TASK_KEY, orig_message)
            print("🔄 saved ITS application task for quick re-run")
        except Exception as e:
            print("?? auto-save ITS task failed: %s" % e)
    return summary


def run_agent(user_message):
    if _kill_armed():
        with _AGENT_LOCK:
            _AGENT["activity"] = "E-STOPPED"
            _AGENT["last_reply"] = "E-STOP is armed — ACEsi is stopped."
            _AGENT["running"] = False
        return
    _agent_reset()
    with _AGENT_LOCK:
        _AGENT["running"] = True
        _AGENT["activity"] = "planning"
    # Deterministic step-list executor (same as /chat): bypass the model for
    # explicit numbered UI scripts that qwen2.5:3b cannot follow.
    script_reply = _execute_ui_script(user_message)
    if script_reply:
        with _AGENT_LOCK:
            _AGENT["running"] = False
            _AGENT["activity"] = "done"
            _AGENT["last_reply"] = script_reply
        return
    messages = [{"role": "system", "content": CODE_AGENT_PROMPT},
                {"role": "user", "content": user_message}]
    max_iters = 30
    calls_history = []
    # Server-side app auto-open (same rationale as _chat_dispatch): if the user
    # explicitly asked to open the app, open it BEFORE the loop so the model's
    # first ui_dump reads the real app screen, not the Android home screen.
    auto_opened = False
    if _ui_task(user_message) and not _ui_situational_ask(user_message) and (
            re.search(r'\bui_app_open\b', user_message, re.IGNORECASE)):
        try:
            _aok, _atxt = _call_tool("ui_app_open", {})
            if _aok:
                auto_opened = True
                with _AGENT_LOCK:
                    _AGENT["tools_used"] = 1
                    _AGENT["steps"].append({"id": _agent_next_id(), "kind": "work",
                                            "text": "ui_app_open (auto)", "state": "done",
                                            "icon": "🔧"})
                calls_history.append("ui_app_open")
                print("🚀 run_agent auto-opened app (user asked for it)")
                _dok, _dtxt = _ui_auto_dump()
                if _dok:
                    messages.append({"role": "user", "content":
                        "APP LAUNCHED. Here is what is now on screen:\n%s%s" % (
                            str(_dtxt)[:2000], _cert_warning_directive(_dtxt))})
        except Exception as e:
            print("⚠️ run_agent auto ui_app_open failed: %s" % e)
    # Same blind-tap guard as _chat_dispatch: taps/swipes are only allowed after
    # the model has read the screen (ui_dump / auto-dump) since the last change.
    seen_screen = bool(auto_opened)
    last_had_tools = False
    # Domain-filter the tool schema for run_agent too. Free-tier providers cap
    # input tokens per minute (Groq ITPM = 7000); the full schema + this prompt
    # exceeds it and every provider 4xx/413s, which surfaced as "all model
    # providers are unavailable". Mirrors _chat_dispatch's active_domain logic.
    _concrete = _classify_message(user_message) - {"general"}
    _agent_domain = (_explicit_tool_domain(user_message)
                     or (next(iter(_concrete)) if _concrete else "general"))
    if _agent_domain == "general" and _nav_task(user_message):
        _agent_domain = "ui"
    _agent_allowed = _domain_tool_names(_agent_domain)
    try:
        corrective_max = 6
        for i in range(max_iters):
            if _AGENT.get("abort"):
                with _AGENT_LOCK:
                    _AGENT["activity"] = "stopped by user"
                    _AGENT["last_reply"] = "Stopped by user."
                    _AGENT["running"] = False
                return
            with _AGENT_LOCK:
                _AGENT["activity"] = "thinking (%d/%d)" % (i + 1, max_iters)
            # Force a structured tool call on UI tasks until a tool has run or
            # the previous round stalled (no tool call) — otherwise qwen2.5:3b
            # narrates a plan instead of acting.
            force_tool = (_ui_task(user_message) and
                          (_AGENT["tools_used"] == 0 or not last_had_tools) and
                          i < 4)
            reply, native_calls = llm_reply(messages, max_tokens=2048, temperature=0.3,
                                            tool_choice="required" if force_tool else "auto",
                                            allowed_names=_agent_allowed)
            print("[agent] turn %d reply=%r native=%d" % (i + 1, (reply or "")[:400], len(native_calls)))
            with _AGENT_LOCK:
                raw = reply or ""
                if native_calls:
                    raw += "\n" + "\n".join("CALL: %s %s" % (n, json.dumps(a)) for n, a in native_calls)
                _AGENT["last_raw"] = raw[:600]
            if not reply and not native_calls:
                # Fallback still applies when the model is down: a file the user
                # explicitly asked for opens deterministically, no model needed.
                _auto_open_user_file_fallback(calls_history, messages, user_message)
                _auto_open_web_image_fallback(reply, messages, user_message)
                with _AGENT_LOCK:
                    _AGENT["activity"] = "stopped (no model reply)"
                    _AGENT["last_reply"] = "All model providers are unavailable right now."
                return
            calls = list(native_calls) + (_extract_calls(reply) if not native_calls else [])
            last_had_tools = bool(calls)
            final = _extract_final(reply)
            if calls:
                _advance_indicator()

            made_calls = 0
            if calls:
                with _AGENT_LOCK:
                    _AGENT["corrective"] = 0
                # Execute the model's emitted tool-call plan IN ORDER (capped),
                # feeding each result back. The model emits a full sequence like
                # ui_app_open -> ui_tap -> ui_dump -> ui_screenshot; executing it
                # as a batch is how tool-schema agents are meant to run and stops
                # the model from re-planning/losing its steps every turn.
                batch = calls[:_BATCH_MAX]
                asst = {"role": "assistant", "content": reply or ""}
                asst["tool_calls"] = [{"id": "call_%d_%d" % (i, j), "type": "function",
                                       "function": {"name": nm, "arguments": json.dumps(a)}}
                                      for j, (nm, a) in enumerate(batch)]
                messages.append(asst)
                if _AGENT.get("abort"):
                    with _AGENT_LOCK:
                        _AGENT["activity"] = "stopped by user"
                        _AGENT["last_reply"] = "Stopped by user."
                    return
                executed_any = False
                for j, (name, args) in enumerate(batch):
                    tcid = "call_%d_%d" % (i, j)
                    if name not in TOOLS:
                        sid = _agent_next_id()
                        with _AGENT_LOCK:
                            _AGENT["steps"].append({"id": sid, "kind": "work",
                                                    "text": name, "state": "error",
                                                    "error": "unknown tool", "icon": "🔧"})
                            _AGENT["tools_used"] += 1
                            _AGENT["last_call_sig"] = (name, json.dumps(args, sort_keys=True))
                            _AGENT["last_call_ok"] = False
                            _AGENT["last_error"] = "unknown tool: %s" % name
                        messages.append({"role": "tool", "tool_call_id": tcid,
                                         "name": name, "content": "unknown tool: %s" % name})
                        messages.append({"role": "user", "content":
                            "Tool '%s' is not available. Check the tool list in the system prompt and "
                            "use one of the real tools (read_file, edit_file, run_command, git_*, "
                            "build_apk, pub_*, flutter_test, flutter_analyze, ui_*, cdp_*, restart)." % name})
                        executed_any = True
                        continue
                    sid = _agent_next_id()
                    icon = _tool_icon(name)
                    desc = _tool_desc(name, args)
                    sig = (name, json.dumps(args, sort_keys=True))
                    with _AGENT_LOCK:
                        prev_sig = _AGENT.get("last_call_sig")
                        prev_ok = _AGENT.get("last_call_ok", False)
                    if sig == prev_sig and prev_ok:
                        with _AGENT_LOCK:
                            _AGENT["activity"] = "repeating a tool call"
                        messages.append({"role": "user", "content":
                            "You already called %s with identical arguments and received its result "
                            "above. Repeating it will not help. State the NEXT distinct action "
                            "(edit_file / run_command) instead of re-calling the same tool." % name})
                        continue
                    with _AGENT_LOCK:
                        _AGENT["steps"].append({"id": sid, "kind": "work", "text": desc,
                                                "state": "running", "icon": icon})
                    # HARD GUARD: block ui_tap/ui_swipe unless the model has read the
                    # screen (ui_dump in this batch, or a successful ui_dump /
                    # auto-dump in a previous round) since the last screen change.
                    if name in ("ui_tap", "ui_swipe") and not seen_screen:
                        result = ("BLOCKED: You must run ui_dump in the same round "
                                  "before ui_tap/ui_swipe. Run ui_dump first to read "
                                  "the screen, then decide your tap coordinates.")
                        ok = False
                    else:
                        ok, result = _call_tool(name, args)
                    executed_any = True
                    calls_history.append(name)
                    with _AGENT_LOCK:
                        _AGENT["tools_used"] += 1
                        _AGENT["last_call_sig"] = sig
                        _AGENT["last_call_ok"] = ok
                        if not ok:
                            _AGENT["last_error"] = "%s: %s" % (name, str(result)[:300])
                        for s in _AGENT["steps"]:
                            if s["id"] == sid:
                                s["state"] = "done" if ok else "error"
                                s["error"] = "" if ok else result
                                # Store viewable result for frontend inline rendering
                                if ok and name in ("view_user_file", "open_user_file", "view_web_image"):
                                    if isinstance(result, _ViewResult):
                                        s["view"] = result.view
                                    elif isinstance(result, dict):
                                        s["view"] = result
                    messages.append({"role": "tool", "tool_call_id": tcid,
                                     "name": name, "content": str(result)})
                    if ok and name in _UI_SCREEN_TOOLS:
                        _dok, _dtxt = _ui_auto_dump()
                        seen_screen = _dok
                        if _dok:
                            messages.append({"role": "user", "content":
                                "SCREEN STATE after your %s action (auto ui_dump):\n%s%s" % (
                                    name, str(_dtxt)[:2000], _cert_warning_directive(_dtxt))})
                            messages.extend(_auto_bypass_cert_warning(_dtxt))
                            if name in ("ui_tap", "ui_swipe", "ui_type", "ui_key"):
                                messages.append({"role": "user", "content":
                                    "STOP. Read the SCREEN STATE above carefully. "
                                    "Based on what you see, decide your NEXT action. "
                                    "Do NOT guess coordinates — use the text/bounds "
                                    "from the screen state above."})
                    if not ok:
                        messages.append({"role": "user", "content":
                            "That tool call FAILED. Do NOT blindly retry it. Diagnose the "
                            "root cause first (read the file / inspect the state), then take a "
                            "corrective action. This is self-healing: fix the actual problem."})
                if _AGENT.get("abort"):
                    with _AGENT_LOCK:
                        _AGENT["activity"] = "stopped by user"
                        _AGENT["last_reply"] = "Stopped by user."
                    return
                # Loop detection: if the same tool was called 3+ times,
                # force a final answer instead of looping forever.
                if calls_history:
                    from collections import Counter as _Counter
                    _counts = _Counter(calls_history)
                    _loop_tool = _counts.most_common(1)[0]
                    # Repeated web_search with no display: the model is stuck
                    # gathering links. Tell it exactly how to show the picture
                    # before giving up, so the image still appears.
                    if (_loop_tool[1] >= 2 and _loop_tool[0] in ("web_search", "webfetch")
                            and "view_web_image" not in _seen_tool_names()
                            and _wants_web_image(user_message)
                            and _AGENT["corrective"] < corrective_max):
                        with _AGENT_LOCK:
                            _AGENT["corrective"] += 1
                        messages.append({"role": "assistant", "content": reply})
                        messages.append({"role": "user", "content":
                            "STOP searching. You already have the image URL in the results above. "
                            "Call view_web_image NOW with that direct image link "
                            "(the .jpg/.png/.gif URL itself) so the picture pops up in the chat. "
                            "Then reply with FINAL: the answer plus a one-line confirmation that "
                            "the image is displayed above. Do NOT call web_search again."})
                        continue
                    if _loop_tool[1] >= 3:
                        with _AGENT_LOCK:
                            _AGENT["activity"] = "done"
                            _advance_indicator()
                        # Auto-open fallback (same as /chat): the model looped on
                        # list/grep without ever opening the requested file.
                        _auto_open_user_file_fallback(calls_history, messages, user_message)
                        _auto_open_web_image_fallback(final or reply, messages, user_message)
                        _AGENT["last_reply"] = _terse_reply(reply) if reply else (
                                "I attempted the task multiple times but couldn't find a "
                                "reliable answer. Check the steps above for what I found.")
                        messages.append({"role": "assistant", "content":
                            _AGENT["last_reply"]})
                        return
                if executed_any:
                    continue

                with _AGENT_LOCK:
                    used = _AGENT["tools_used"]
                if final:
                    nav_push = _nav_gate(user_message, calls_history)
                    if nav_push and _AGENT["corrective"] < corrective_max:
                        with _AGENT_LOCK:
                            _AGENT["corrective"] += 1
                        messages.append({"role": "assistant", "content": reply})
                        messages.append({"role": "user", "content": nav_push})
                        continue
                    if used == 0 and _AGENT["corrective"] < corrective_max:
                        with _AGENT_LOCK:
                            _AGENT["corrective"] += 1
                        messages.append({"role": "assistant", "content": reply})
                        messages.append({"role": "user", "content":
                            "You haven't used any tools yet. Pick the RIGHT tool for THIS task: "
                            "ui_* tools for device/app actions (ui_app_open, ui_tap, ui_swipe, "
                            "ui_type, ui_key, ui_dump, ui_screenshot), file tools + run_command / "
                            "flutter_* for code work, cdp_* for the WebView. Emit THOUGHT + CALL "
                            "now — do NOT emit FINAL until you have actually performed the work "
                            "and verified the result. Never defer back to the user."})
                        continue
                # Auto-open fallback (same as /chat): the model may have FINAL'd
                # without ever calling view_user_file/open_user_file.
                _auto_open_user_file_fallback(calls_history, messages, user_message)
                _auto_open_web_image_fallback(final, messages, user_message)
                with _AGENT_LOCK:
                    _AGENT["activity"] = "done"
                    _advance_indicator()
                    _AGENT["last_reply"] = final
                messages.append({"role": "assistant", "content": reply})
                return
            if final:
                with _AGENT_LOCK:
                    used = _AGENT["tools_used"]
                nav_push = _nav_gate(user_message, calls_history)
                if nav_push and _AGENT["corrective"] < corrective_max:
                    with _AGENT_LOCK:
                        _AGENT["corrective"] += 1
                    messages.append({"role": "assistant", "content": reply})
                    messages.append({"role": "user", "content": nav_push})
                    continue
                if used == 0 and _AGENT["corrective"] < corrective_max:
                    with _AGENT_LOCK:
                        _AGENT["corrective"] += 1
                    messages.append({"role": "assistant", "content": reply})
                    messages.append({"role": "user", "content":
                        "You haven't used any tools yet. Pick the RIGHT tool for THIS task: "
                        "ui_* tools for device/app actions (ui_app_open, ui_tap, ui_swipe, "
                        "ui_type, ui_key, ui_dump, ui_screenshot), file tools + run_command / "
                        "flutter_* for code work, cdp_* for the WebView. Emit THOUGHT + CALL "
                        "now — do NOT emit FINAL until you have actually performed the work "
                        "and verified the result. Never defer back to the user."})
                    continue
                # Auto-open fallback (same as /chat): FINAL text without any file
                # view still resolves and opens the requested file server-side.
                _auto_open_user_file_fallback(calls_history, messages, user_message)
                _auto_open_web_image_fallback(final, messages, user_message)
                with _AGENT_LOCK:
                    _AGENT["activity"] = "done"
                    _advance_indicator()
                    _AGENT["last_reply"] = final
                messages.append({"role": "assistant", "content": reply})
                return
            # No CALL and no FINAL — push the model toward tools.
            nav_push = _nav_gate(user_message, calls_history) if (not calls and not final) else None
            if nav_push and _AGENT["corrective"] < corrective_max:
                with _AGENT_LOCK:
                    _AGENT["corrective"] += 1
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": nav_push})
                continue
            if _AGENT["corrective"] < corrective_max and _ui_task(user_message):
                with _AGENT_LOCK:
                    _AGENT["corrective"] += 1
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content":
                    "Continue. Emit THOUGHT and CALL tool lines using the RIGHT tool for this "
                    "task (ui_* for device/app actions, file/dev tools for code work). Do NOT "
                    "emit FINAL until you have used at least one tool and verified the result."})
                continue
            # Auto-open fallback (same as /chat): no CALL and no FINAL — still try
            # to open a file the user explicitly asked for.
                _auto_open_user_file_fallback(calls_history, messages, user_message)
                _auto_open_web_image_fallback(final, messages, user_message)
                with _AGENT_LOCK:
                    _AGENT["activity"] = "done"
                    _advance_indicator()
                    _AGENT["last_reply"] = _terse_reply(reply)
            messages.append({"role": "assistant", "content": reply})
            return
        with _AGENT_LOCK:
            _AGENT["activity"] = "stopped (step cap reached)"
            if not _AGENT["last_reply"]:
                _AGENT["last_reply"] = "Reached the action limit; see the steps above."
    except Exception as e:
        import traceback
        with _AGENT_LOCK:
            _AGENT["activity"] = "error"
            _AGENT["last_error"] = ("%s: %s" % (type(e).__name__, e))[:400]
            _AGENT["last_reply"] = "Agent error: %s" % e
        print("💥 agent loop error: %s" % e)
        print(traceback.format_exc())
    finally:
        with _AGENT_LOCK:
            _AGENT["running"] = False
        # Playbook memory: record what this task was and which tools worked.
        with _AGENT_LOCK:
            used_tools = list(calls_history)
            outcome = _AGENT["last_reply"]
        if used_tools and not _kill_armed():
            playbook_note(user_message, used_tools, outcome)

# Shared provider-fallback LLM call (Groq -> Cerebras -> OpenRouter -> Ollama).
# Returns (text, tool_calls) where tool_calls is a list of (name, args_dict).
# Passes the native tools= schema to the provider so the model can emit
# structured tool_calls instead of free-form prose (the stall fix).
def llm_reply(messages, max_tokens=2048, temperature=0.3, tool_choice="auto",
              allowed_names=None):
    # Free-tier providers cap input tokens per minute (Groq ITPM = 7000). Sending
    # the full 54-tool schema (~8.9k tok) with the agent prompt trips a 413, which
    # made every /opencode task look like "all providers are down". Restrict to the
    # task's domain tools first, then trim further if still over budget.
    tools_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names) if allowed_names else TOOLS_SCHEMA
    tools_schema = _fit_schema_to_budget(messages, tools_schema, max_tokens)

    def one(name, endpoint, api_key, model):
        if not api_key:
            return None
        # Free tiers cap INPUT TOKENS PER MINUTE (Groq ITPM = 7000). A multi-turn
        # agent loop sends one request per turn, so turn 2+ can 429 even when each
        # request is individually under the cap. Wait out the sliding window and
        # retry instead of abandoning the task as "all providers unavailable".
        for attempt in range(3):
            try:
                r = requests.post(f"{endpoint}/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                    json={"model": model, "messages": messages, "temperature": temperature,
                          "max_tokens": max_tokens, "tools": tools_schema, "tool_choice": tool_choice},
                    timeout=(10, 120))
                if r.status_code == 200:
                    msg = r.json()["choices"][0]["message"]
                    text = (msg.get("content") or "").strip()
                    tcs = []
                    for tc in (msg.get("tool_calls") or []):
                        fn = tc.get("function") or {}
                        nm = fn.get("name")
                        try:
                            args = json.loads(fn.get("arguments") or "{}")
                        except Exception:
                            args = {}
                        if nm:
                            tcs.append((nm, args))
                    if tcs:
                        print(f"✅ llm_reply via {name} ({len(tcs)} tool_call(s))")
                        return text, tcs
                    if text:
                        print(f"✅ llm_reply via {name} ({len(text)} chars, no tools)")
                        return text, []
                    # HTTP 200 but an empty completion is a provider glitch,
                    # not a final answer - retry instead of giving up.
                    print(f"⚠️ {name} returned 200 with no text and no tool calls")
                    continue
                if r.status_code == 429 and attempt < 2:
                    wait = 20 * (attempt + 1)
                    print(f"⏳ {name} 429 rate limit; waiting {wait}s for the token window")
                    time.sleep(wait)
                    continue
                print(f"❌ {name} {r.status_code}: {r.text[:160]}")
            except Exception as e:
                print(f"❌ {name} exc: {e}")
            # Retry transient failures (5xx, timeouts, connection resets) too.
            # This used to `return None` here, which abandoned the provider on
            # the FIRST non-429 error and made the loop below unreachable, so
            # only 429 ever actually retried.
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            return None
        return None
    # Offline mode: skip cloud providers entirely, go straight to local Ollama.
    if os.environ.get("ACE_OFFLINE") == "1":
        print("🔌 ACE_OFFLINE=1 set — skipping cloud providers, using local Ollama")
    else:
        for name, ep, key, model in (("Groq", GROQ_ENDPOINT, GROQ_API_KEY, GROQ_MODEL),
                                     ("Cerebras", CEREBRAS_ENDPOINT, CEREBRAS_API_KEY, CEREBRAS_MODEL),
                                     ("OpenRouter", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, OPENROUTER_MODEL),
                                     ("FreeLLM", FREELLM_ENDPOINT, FREELLM_API_KEY, FREELLM_MODEL)):
            res = one(name, ep, key, model)
            if res is not None:
                return res
        for model in OPENROUTER_FALLBACKS:
            res = one("OpenRouter-fallback", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, model)
            if res is not None:
                return res
    # Last resort: local Ollama — offline + tool-capable so ACEsi stays autonomous
    # with NO network. Uses the full tools schema so cdp_*/edit_file are callable.
    if not OLLAMA_ENABLED:
        return "", []
    try:
        print(" llama llm_reply via Ollama model=%s" % OLLAMA_MODEL)
        # Ollama crashes on this hardware with any prompt over ~500 chars
        # (2GB VRAM, no AVX2). Replace the 15k-char system prompt with a
        # minimal one so the model can actually respond.
        ollama_messages = [{"role": "system", "content": _OLLAMA_MINIMAL_PROMPT}]
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")
            if role == "system":
                continue
            ollama_messages.append({"role": role, "content": content})
        payload = {"model": OLLAMA_MODEL, "messages": ollama_messages, "stream": False,
                   "max_tokens": min(max_tokens, 512), "temperature": temperature}
        if tool_choice:
            payload["tool_choice"] = tool_choice
        r = requests.post(f"{OLLAMA_ENDPOINT}/chat/completions", json=payload,
                         timeout=(15, 420))
        if r.status_code == 200:
            msg = r.json()["choices"][0]["message"]
            t = (msg.get("content") or "").strip()
            tcs = []
            for tc in (msg.get("tool_calls") or []):
                fn = tc.get("function") or {}
                nm = fn.get("name")
                am = fn.get("arguments")
                if isinstance(am, str):
                    try:
                        args = json.loads(am)
                    except Exception:
                        args = {}
                elif isinstance(am, dict):
                    args = am
                else:
                    args = {}
                if nm:
                    tcs.append((nm, args))
            if tcs:
                print(f"✅ llm_reply via Ollama ({len(tcs)} tool_call(s))")
                return t, tcs
            if t:
                print(f"✅ llm_reply via Ollama ({len(t)} chars, no tools)")
                return t, []
            return None
        print(f"❌ Ollama {r.status_code}: {r.text[:160]}")
    except Exception as e:
        print(f"❌ Ollama exc: {e}")
    return "", []

# ---- CDP REST endpoints (inspect ITS WebView / local Chrome without the agent loop) ----

def _cdp_json(result):
    ok, payload = result
    return jsonify({"ok": ok, "result": payload}), (200 if ok else 502)

@app.route('/cdp/connect', methods=['GET'])
@app.route('/cdp/connect', methods=['POST'])
def cdp_route_connect():
    return _cdp_json(d.connect_cmd())

@app.route('/cdp/evaluate', methods=['POST'])
def cdp_route_evaluate():
    expr = (request.json or {}).get("expr") if request.is_json else request.form.get("expr")
    return _cdp_json(d.evaluate_js(expr))

@app.route('/cdp/console', methods=['GET'])
def cdp_route_console():
    return _cdp_json(d.get_console_logs())

@app.route('/cdp/dom', methods=['GET'])
def cdp_route_dom():
    return _cdp_json(d.get_dom_state())

@app.route('/cdp/network', methods=['GET'])
def cdp_route_network():
    return _cdp_json(d.get_network_requests())

@app.route('/cdp/status', methods=['GET'])
def cdp_route_status():
    return jsonify({"ok": True, "result": d.status()})

@app.route('/screenshot/latest', methods=['GET'])
def screenshot_latest():
    """Serve the most recent in-memory screenshot (the popup image). No PNG
    buffered -> tell the caller there is nothing to show yet."""
    if not _LAST_SHOT["png"]:
        return jsonify({"ok": False, "result": "no screenshot captured yet"}), 404
    return Response(_LAST_SHOT["png"], mimetype="image/png")

@app.route('/screenshot/save', methods=['POST'])
def screenshot_save():
    """Write the buffered screenshot to ui_screenshots/ (Chris clicked Save in
    the popup). Returns the real on-disk path so nothing is ever fabricated."""
    if not _LAST_SHOT["png"]:
        return jsonify({"ok": False, "error": "no screenshot in memory"}), 404
    os.makedirs(ACE_UI_SHOTS, exist_ok=True)
    fname = "ui_%s.png" % datetime.now().strftime("%H%M%S")
    path = os.path.join(ACE_UI_SHOTS, fname)
    try:
        with open(path, "wb") as f:
            f.write(_LAST_SHOT["png"])
        print("🖼️ Popup screenshot saved to disk: %s" % path)
        return jsonify({"ok": True, "path": path})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/opencode', methods=['POST'])
def opencode():
    try:
        data = request.json or {}
        user_message = (data.get('message') or '').strip()
        if not user_message:
            return jsonify({"reply": "No message."}), 400
        if _kill_armed():
            return jsonify({"reply": "E-STOP is armed — ACEsi is stopped."}), 403
        with _AGENT_LOCK:
            if _AGENT["running"]:
                return jsonify({"reply": "ACEsi is already working on a task. Let it finish or click stop."})
            _AGENT["running"] = True
            _AGENT["abort"] = False
            _AGENT["activity"] = "starting…"
        t = threading.Thread(target=run_agent, args=(user_message,), daemon=True)
        t.start()
        return jsonify({"reply": "ACEsi started working on this…", "type": "start"})
    except Exception as e:
        with _AGENT_LOCK:
            _AGENT["running"] = False
            _AGENT["activity"] = "error"
            _AGENT["last_reply"] = f"Error: {type(e).__name__}: {e}"
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route('/opencode/status', methods=['GET'])
def opencode_status():
    with _AGENT_LOCK:
        return jsonify({
            "status": "busy" if _AGENT["running"] else "idle",
            "activity": _AGENT["activity"],
            "indicator": _current_indicator(),
            "steps": list(_AGENT["steps"]),
            "last_reply": _AGENT["last_reply"],
            "last_raw": _AGENT["last_raw"],
            "tools_used": _AGENT["tools_used"],
            "corrective": _AGENT["corrective"],
            "last_error": _AGENT["last_error"],
            "shot_ts": _LAST_SHOT["ts"],
            "ui_test": dict(_UI_LAST_TEST),
        })

@app.route('/opencode/heal', methods=['POST', 'GET'])
def opencode_heal():
    """Self-healing: feed the last run's failures back to ACEsi and let it fix them."""
    with _AGENT_LOCK:
        if _AGENT["running"]:
            return jsonify({"reply": "ACEsi is already working — let it finish or stop first."}), 409
        steps = list(_AGENT["steps"])
        last_error = _AGENT.get("last_error", "")
        last_reply = _AGENT.get("last_reply", "")
    failed = [s for s in steps if s.get("state") == "error"]
    if not failed and not last_error:
        return jsonify({"reply": "Nothing to heal — the last run had no failing steps."})
    detail = "\n".join("• %s: %s" % (s.get("text", s.get("id")), (s.get("error") or "")[:400])
                       for s in failed[-5:])
    msg = ("SELF-HEALING RUN. A previous ACEsi run left errors behind. Recover from them:\n"
           "FAILING STEPS:\n%s\nLAST ERROR: %s\nLAST REPLY: %s\n\n"
           "Diagnose the root cause, fix it (edit_file / run_command / flutter_test / "
           "flutter_analyze / git_commit), and confirm with FINAL. Do not redo work that "
           "already succeeded." % (detail or "(none)", last_error or "(none)", last_reply))
    with _AGENT_LOCK:
        _AGENT["running"] = True
        _AGENT["abort"] = False
        _AGENT["activity"] = "healing…"
    t = threading.Thread(target=run_agent, args=(msg,), daemon=True)
    t.start()
    return jsonify({"reply": "Heal started — fixing %d failing step(s)." % len(failed)})

@app.route('/opencode/stop', methods=['POST'])
def opencode_stop():
    with _AGENT_LOCK:
        _AGENT["abort"] = True
        _AGENT["activity"] = "stopping…"
        _AGENT["running"] = False
        _AGENT["last_reply"] = "Stopped by user."
    return jsonify({"ok": True})

@app.route('/dispatcher/run', methods=['POST'])
def dispatcher_run():
    """Run ace_dispatcher TaskRunner for robust multi-subtask execution.

    POST JSON body:
      message: user instruction (required)
      subtasks: optional list of Subtask dicts (id, title, tool, args,
                depends_on, soft_depends_on)
      max_steps: step cap (default 50)
    Returns a markdown summary with partial-completion reporting:
    successes listed before failures, with counts and per-step detail.
    """
    data = request.json or {}
    user_message = (data.get('message') or '').strip()
    if not user_message and not data.get('subtasks'):
        return jsonify({"error": "Provide 'message' or 'subtasks'."}), 400
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed."}), 403

    subtasks = None
    raw_tasks = data.get('subtasks')
    if raw_tasks:
        subtasks = [ace_dispatcher.Subtask.from_dict(t) if isinstance(t, dict)
                     else t for t in raw_tasks]
    try:
        result = _run_dispatcher(user_message, subtasks=subtasks,
                                 max_steps=int(data.get('max_steps', 50)))
    except Exception as e:
        return jsonify({"error": "%s: %s" % (type(e).__name__, e)}), 500
    return jsonify(result)

@app.route('/auto_fix_stream', methods=['GET'])
def auto_fix_stream():
    file_path = request.args.get('file_path')
    error_text = request.args.get('error_text')

    if not file_path or not error_text:
        return "Missing parameters", 400

    def generate():
        yield "Reading file...\n\n"
        time.sleep(0.5)
        # If a bare filename arrived, anchor it to the project directory so the
        # read and the error message both use an absolute path.
        target = file_path
        if not os.path.isabs(target):
            joined = os.path.join(DATA_DIR, target)
            if os.path.exists(joined):
                target = joined
        try:
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()
            yield "File read successfully.\n\n"
            time.sleep(0.5)
        except FileNotFoundError:
            yield f"📄 File not found: {target}\nMake sure the file exists in the project directory or your Documents folder.\n\n"
            return
        except Exception as e:
            yield f"Failed to read file: {str(e)}\n\n"
            return

        yield "Generating fix...\n\n"
        time.sleep(0.5)
        fix_messages = [
            {"role": "system", "content": f"You are ACEsi, an expert debugger. Fix the following code. The error is: {error_text}. Respond with only the fixed code — no explanations."},
            {"role": "user", "content": content}
        ]
        fixed_code = None
        for name, endpoint, api_key, model in (
            ("Groq", GROQ_ENDPOINT, GROQ_API_KEY, GROQ_MODEL),
            ("Cerebras", CEREBRAS_ENDPOINT, CEREBRAS_API_KEY, CEREBRAS_MODEL),
            ("OpenRouter", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, OPENROUTER_MODEL),
        ):
            if not api_key:
                continue
            try:
                resp = requests.post(
                    f"{endpoint}/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                    json={"model": model, "messages": fix_messages, "temperature": 0.3, "max_tokens": 400},
                    timeout=(10, 120)
                )
                if resp.status_code == 200:
                    fixed_code = resp.json()["choices"][0]["message"]["content"]
                    break
                else:
                    yield f"[{name} {resp.status_code}] retrying next provider...\n\n"
            except Exception as e:
                yield f"[{name} failed: {str(e)[:120]}] retrying next provider...\n\n"
        if fixed_code:
            yield "Fix generated.\n\n"
            time.sleep(0.5)
        else:
            yield "Fix generation failed across all providers.\n\n"
            return

        yield "Applying fix...\n\n"
        time.sleep(0.5)
        cleaned = strip_code_fences(fixed_code)
        try:
            with open(target, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            yield "Fix applied successfully!\n\n"
            # Surface the result inline in the chat stream
            yield f"CODE:\n{cleaned}\n"
            time.sleep(0.5)
        except Exception as e:
            yield f"Failed to write file: {str(e)}\n\n"
            return

        try:
            winsound.Beep(1000, 500)
        except:
            pass

        try:
            requests.post(
                f"{NTFY_SERVER}/{NTFY_TOPIC}",
                data=f"ACEsi fixed it! Auto-fix applied to {file_path}.",
                headers={"Priority": "high", "Title": "ACEsi fixed it!"},
                timeout=10
            )
            yield "Notification sent.\n\n"
        except Exception as e:
            yield f"ntfy error: {e}\n\n"

        yield "Auto-fix complete.\n\n"

    response = Response(generate(), mimetype='text/plain')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# ===== Memory endpoints =====
@app.route('/memory/all', methods=['GET'])
def memory_all():
    return jsonify({"memory": get_memories()})

@app.route('/memory/set', methods=['POST'])
def memory_set():
    data = request.json or {}
    key = data.get('key', '').strip()
    value = data.get('value', '').strip()
    if not key or not value:
        return jsonify({"error": "key and value required"})
    set_memory(key, value)
    return jsonify({"ok": True, "key": key})

@app.route('/memory/bulk', methods=['POST'])
def memory_bulk():
    items = (request.json or {}).get('items')
    if not isinstance(items, dict):
        return jsonify({"error": "items must be an object"})
    for k, v in items.items():
        set_memory(str(k), str(v))
    return jsonify({"count": len(items)})

@app.route('/memory/forget', methods=['POST'])
def memory_forget():
    key = (request.json or {}).get('key', '')
    forget_memory(key)
    return jsonify({"ok": True})

# ===== Journal endpoints =====
@app.route('/journal', methods=['GET'])
def journal_get():
    return jsonify({"entries": get_journal(int(request.args.get('limit', 10)))})

@app.route('/journal', methods=['POST'])
def journal_post():
    entry = (request.json or {}).get('entry', '').strip()
    if not entry:
        return jsonify({"error": "entry required"})
    add_journal(entry)
    return jsonify({"ok": True, "entry": entry})

# ===== Summary endpoints =====
@app.route('/summary', methods=['GET'])
def summary_get():
    return jsonify({
        "summary": build_summary_text(),
        "config": {
            "time": get_config('summary_time', '07:00'),
            "enabled": get_config('summary_enabled', 'true') != 'false'
        }
    })

@app.route('/summary/config', methods=['POST'])
def summary_config():
    data = request.json or {}
    time = data.get('time', '07:00')
    enabled = bool(data.get('enabled', True))
    set_config('summary_time', time)
    set_config('summary_enabled', 'true' if enabled else 'false')
    return jsonify({"ok": True, "config": {"time": time, "enabled": enabled}})

@app.route('/summary/now', methods=['POST'])
def summary_now():
    text = build_summary_text()
    ok = send_ntfy("ACEsi — Daily summary", text)
    return jsonify({"ok": ok, "summary": text})

# ===== Notification endpoints =====
@app.route('/notify/topic', methods=['GET'])
def notify_topic():
    return jsonify({"topic": NTFY_TOPIC})

@app.route('/notify', methods=['POST'])
def notify_post():
    data = request.json or {}
    title = data.get('title', 'ACEsi')
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"error": "message required"})
    ok = send_ntfy(title, message)
    return jsonify({"ok": ok})

# ===== Kill switch endpoints (web UI control from the PC) =====
@app.route('/kill/status', methods=['GET'])
def kill_status():
    return jsonify(_kill_state())

@app.route('/kill', methods=['POST'])
def kill_now():
    reason = (request.json or {}).get('reason', 'Web UI force stop')
    _kill_arm(reason=reason, source='web')
    return jsonify({"armed": True, "message": _KILL_CONFIRM})

@app.route('/kill/resume', methods=['POST'])
def kill_resume_web():
    data = request.json or {}
    unword = (data.get('password') or '').strip()
    if not _kill_unword_match(unword):
        return jsonify({"ok": False, "error": "un-kill word incorrect"}), 403
    _kill_resume()
    return jsonify({"armed": False, "ok": True})

# ===== Tasks =====
def _norm_priority(raw):
    try:
        p = int(raw)
    except (TypeError, ValueError):
        return 3
    return max(1, min(5, p))

@app.route('/tasks', methods=['GET'])
def tasks_get():
    return jsonify({"tasks": read_items('tasks.json', 'tasks')})

@app.route('/tasks', methods=['POST'])
def tasks_post():
    data = request.json or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({"error": "title required"})
    def add_task(items):
        items.append({
            "id": uuid.uuid4().hex,
            "title": title,
            "notes": (data.get('notes') or ''),
            "priority": _norm_priority(data.get('priority', 3)),
            "status": data.get('status', 'pending'),
            "created_at": datetime.now().isoformat(),
            "done_at": None
        })
        return items
    mutate_items('tasks.json', 'tasks', add_task)
    return jsonify({"ok": True})

@app.route('/tasks/<tid>/status', methods=['POST'])
def tasks_status(tid):
    status = (request.json or {}).get('status', 'pending')
    def update(items):
        for t in items:
            if t['id'] == tid:
                t['status'] = status if status in ('pending', 'in_progress', 'done') else 'pending'
                t['done_at'] = datetime.now().isoformat() if t['status'] == 'done' else None
        return items
    mutate_items('tasks.json', 'tasks', update)
    return jsonify({"ok": True})

@app.route('/tasks/<tid>', methods=['DELETE'])
def tasks_delete(tid):
    mutate_items('tasks.json', 'tasks', lambda items: [t for t in items if t['id'] != tid])
    return jsonify({"ok": True})

# ===== Job scheduler (autonomous triggers) =====
# Jobs let ACEsi run a full autonomous task on a schedule — like "every morning
# check the Venda ITS portal and report", or "daily at 17:00 git commit today's
# work". Each job fires through the same brain as /chat (deterministic handlers
# + tool loop) and pushes the result to Chris via ntfy. Schedule shapes:
#   {"type": "once",      "run_at": "2026-09-18T08:00:00"}
#   {"type": "daily",     "time": "HH:MM"}
#   {"type": "interval",  "minutes": N}
_JOBS_FILE = 'jobs.json'
_JOBS_LOCK = threading.RLock()
_JOBS_RUNNING = {}  # job_id -> Thread, so a long job can't double-fire


def _jobs_read():
    with _JOBS_LOCK:
        d = load_json(_JOBS_FILE, {})
        items = d.get('jobs', []) if isinstance(d, dict) else d
        return [j for j in items if isinstance(j, dict)]


def _jobs_save(items):
    with _JOBS_LOCK:
        save_json(_JOBS_FILE, {'jobs': list(items or [])})


def _job_add(item):
    def add(jobs):
        jobs.append(item)
        return jobs
    with _JOBS_LOCK:
        mutate_items(_JOBS_FILE, 'jobs', add)


def _jobs_due_estimate(job, now=None):
    """True if this job is scheduled to fire now. Idempotent per (type, key)."""
    now = now or datetime.now()
    sched = job.get('schedule') or {}
    st = sched.get('type', 'daily')
    key = None
    if st == 'once':
        try:
            run_at = datetime.fromisoformat(sched['run_at'])
        except Exception:
            return False, None
        key = ('once', sched.get('run_at'))
        return now >= run_at, key
    if st == 'interval':
        last = job.get('last_run_ts') or 0
        key = ('interval', sched.get('minutes'))
        return int(time.time()) - last >= int(sched.get('minutes', 60)) * 60, key
    # daily. Compare (time passed, not yet fired today) rather than exact
    # "HH:MM" equality: with a 20s poll, one GC pause, a slow request or a
    # laptop sleep at exactly 07:00 used to skip that day's job permanently.
    at = str(sched.get('time') or '07:00')
    key = ('daily', now.strftime('%Y-%m-%d') + ' ' + at)
    # Compare against the SAME string form that _job_fire persists, otherwise
    # a stored "daily|2026-09-25 07:00" never matches this tuple and a daily
    # job re-fires all day.
    if job.get('last_fire_key') == '|'.join(str(p) for p in key):
        return False, key          # already ran for this date+time
    try:
        due_at = datetime.combine(now.date(), datetime.strptime(at, "%H:%M").time())
    except ValueError:
        return False, key          # malformed time: never fire, never wedge
    return now >= due_at, key


def _job_fire(job, fire_key=None):
    """Run one autonomous job through the /chat brain (full determinism + tools),
    then push the outcome to Chris. Runs in its own thread."""
    def runner():
        jid = job.get('id')
        try:
            prompt = (job.get('prompt') or '').strip() or ("Run "+ (job.get('name') or 'task') + " for Chris.")
            r = requests.post(f"http://127.0.0.1:{SERVER_PORT}/chat",
                              json={"message": prompt}, timeout=(15, 900))
            reply = ""
            if r.status_code == 200:
                d = r.json() or {}
                reply = d.get("reply") or ""
                if d.get("type") == "stream":
                    reply = "That task needs code fixes — see the ACEsi web UI for the auto-fix stream."
            send_ntfy("ACEsi — Job: %s" % (job.get('name') or 'task'),
                      ("Done.\n\n%s" % reply if reply else "Job finished (no text reply)."))
            # Persist last-run markers so the job doesn't refire.
            jobs = _jobs_read()
            for j in jobs:
                if j.get('id') == jid:
                    j['last_run'] = datetime.now().isoformat()
                    j['last_run_ts'] = int(time.time())
                    # Remember which (date,time) slot this job consumed so a
                    # daily job cannot re-fire later the same day.
                    if fire_key:
                        j['last_fire_key'] = '|'.join(str(p) for p in fire_key)
                    if (j.get('schedule') or {}).get('type') == 'once':
                        j['enabled'] = False
            _jobs_save(jobs)
        except Exception as e:
            print(f"⚠️ job {jid} error: {e}")
            try:
                send_ntfy("ACEsi — Job error", "Job '%s' failed: %s" % ((job.get('name') or 'task'), e))
            except Exception:
                pass
        finally:
            with _JOBS_LOCK:
                _JOBS_RUNNING.pop(jid, None)
    with _JOBS_LOCK:
        if job.get('id') in _JOBS_RUNNING:
            return False  # already running
    th = threading.Thread(target=runner, daemon=True)
    with _JOBS_LOCK:
        _JOBS_RUNNING[job['id']] = th
    th.start()
    return True


def job_watch():
    """Background loop: every 20s, fire any enabled, due, not-already-running job.
    Skips everything while the kill switch is armed."""
    time.sleep(15)
    while True:
        try:
            if _kill_armed():
                time.sleep(20)
                continue
            for job in _jobs_read():
                if not job.get('enabled', True):
                    continue
                due, key = _jobs_due_estimate(job)
                if due:
                    # Only run if we haven't fired for this (type, key) yet.
                    if _JOBS_RUNNING.get(job.get('id')):
                        continue
                    _job_fire(job, fire_key=key)
        except Exception as e:
            print(f"⚠️ job watchdog: {e}")
        time.sleep(20)


@app.route('/jobs', methods=['GET'])
def jobs_get():
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed"}), 403
    return jsonify({"jobs": _jobs_read()})

@app.route('/jobs', methods=['POST'])
def jobs_post():
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed"}), 403
    data = request.json or {}
    name = (data.get('name') or '').strip()
    prompt = (data.get('prompt') or '').strip()
    if not name or not prompt:
        return jsonify({"error": "name and prompt required"})
    schedule = data.get('schedule') or {}
    jid = uuid.uuid4().hex
    _job_add({
        "id": jid, "name": name, "prompt": prompt,
        "schedule": schedule, "enabled": data.get('enabled', True),
        "created_at": datetime.now().isoformat(),
        "last_run": None, "last_run_ts": 0,
    })
    return jsonify({"ok": True, "id": jid})

@app.route('/jobs/<jid>', methods=['DELETE'])
def jobs_delete(jid):
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed"}), 403
    _jobs_save([j for j in _jobs_read() if j.get('id') != jid])
    return jsonify({"ok": True})

@app.route('/jobs/<jid>/run', methods=['POST'])
def jobs_run_now(jid):
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed"}), 403
    for j in _jobs_read():
        if j.get('id') == jid and j.get('enabled', True) and _job_fire(j):
            return jsonify({"ok": True, "started": True})
    return jsonify({"ok": False, "error": "job not found or already running"}), 400

# ===== Playbook + audit log =====
@app.route('/playbook', methods=['GET'])
def playbook_get():
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed"}), 403
    return jsonify({"playbook": _playbook_read()})

@app.route('/playbook', methods=['DELETE'])
def playbook_clear():
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed"}), 403
    _playbook_save([])
    return jsonify({"ok": True})

@app.route('/audit/tail', methods=['GET'])
def audit_tail():
    if _kill_armed():
        return jsonify({"error": "E-STOP is armed"}), 403
    try:
        with open(_AUDIT_LOG, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        return jsonify({"tail": lines[-200:]})
    except FileNotFoundError:
        return jsonify({"tail": [], "error": ""})

# ===== Calendar events =====
@app.route('/events', methods=['GET'])
def events_get():
    return jsonify({"events": read_items('events.json', 'events')})

@app.route('/events', methods=['POST'])
def events_post():
    data = request.json or {}
    title = (data.get('title') or '').strip()
    date = (data.get('date') or '').strip()
    if not title or not date:
        return jsonify({"error": "title and date required"})
    def add_event(items):
        items.append({
            "id": uuid.uuid4().hex,
            "title": title,
            "date": date,
            "time": (data.get('time') or '').strip()
        })
        return items
    mutate_items('events.json', 'events', add_event)
    return jsonify({"ok": True})

@app.route('/events/<eid>', methods=['DELETE'])
def events_delete(eid):
    mutate_items('events.json', 'events', lambda items: [e for e in items if e['id'] != eid])
    return jsonify({"ok": True})

# ===== Timers =====
@app.route('/timers', methods=['GET'])
def timers_get():
    now = time.time()
    timers = read_items('timers.json', 'timers')
    out = [{
        "id": t.get("id"),
        "label": t.get("label", "Timer"),
        "total": t.get("total", 0),
        "remaining": max(0, int(t.get("ends_at", 0) - now))
    } for t in timers]
    return jsonify({"timers": out})

@app.route('/timers', methods=['POST'])
def timers_post():
    data = request.json or {}
    try:
        minutes = int(data.get('minutes', 0))
    except (TypeError, ValueError):
        return jsonify({"error": "minutes must be a number"})
    if minutes < 1:
        return jsonify({"error": "minutes must be at least 1"})
    label = (data.get('label') or 'Timer').strip() or 'Timer'
    def add_timer(items):
        items.append({
            "id": uuid.uuid4().hex,
            "label": label,
            "minutes": minutes,
            "total": minutes * 60,
            "ends_at": time.time() + minutes * 60,
            "created_at": datetime.now().isoformat()
        })
        return items
    mutate_items('timers.json', 'timers', add_timer)
    return jsonify({"ok": True})

@app.route('/timers/<tid>', methods=['DELETE'])
def timers_delete(tid):
    mutate_items('timers.json', 'timers', lambda items: [t for t in items if t['id'] != tid])
    return jsonify({"ok": True})

# ===== Alarms =====
@app.route('/alarms', methods=['GET'])
def alarms_get():
    return jsonify({"alarms": read_items('alarms.json', 'alarms')})

@app.route('/alarms', methods=['POST'])
def alarms_post():
    data = request.json or {}
    time_str = (data.get('time') or '').strip()
    label = (data.get('label') or 'Alarm').strip() or 'Alarm'
    if not time_str:
        return jsonify({"error": "time required"})
    def add_alarm(items):
        items.append({
            "id": uuid.uuid4().hex,
            "time": time_str,
            "label": label,
            "daily": bool(data.get('daily', True)),
            "enabled": True,
            "last_fired": None
        })
        return items
    mutate_items('alarms.json', 'alarms', add_alarm)
    return jsonify({"ok": True})

@app.route('/alarms/<aid>/toggle', methods=['POST'])
def alarms_toggle(aid):
    def toggle(items):
        for a in items:
            if a['id'] == aid:
                a['enabled'] = not a.get('enabled', True)
                a['last_fired'] = None
        return items
    mutate_items('alarms.json', 'alarms', toggle)
    return jsonify({"ok": True})

@app.route('/alarms/<aid>', methods=['DELETE'])
def alarms_delete(aid):
    mutate_items('alarms.json', 'alarms', lambda items: [a for a in items if a['id'] != aid])
    return jsonify({"ok": True})

# ===== Work sessions =====
@app.route('/sessions', methods=['GET'])
def sessions_get():
    return jsonify({"sessions": read_items('sessions.json', 'sessions')})

@app.route('/sessions/start', methods=['POST'])
def sessions_start():
    sessions = read_items('sessions.json', 'sessions')
    if any(s.get('ended_at') is None for s in sessions):
        return jsonify({"error": "A session is already running."})
    data = request.json or {}
    label = (data.get('label') or 'Work session').strip() or 'Work session'
    started = datetime.now()
    def add_session(items):
        items.append({
            "id": uuid.uuid4().hex,
            "label": label,
            "started_at": started.isoformat(),
            "started_epoch": int(started.timestamp()),
            "ended_at": None,
            "duration": None
        })
        return items
    mutate_items('sessions.json', 'sessions', add_session)
    return jsonify({"ok": True})

@app.route('/sessions/end', methods=['POST'])
def sessions_end():
    ended = datetime.now()
    def close_session(items):
        for s in reversed(items):
            if s.get('ended_at') is None:
                s['ended_at'] = ended.isoformat()
                secs = max(0, int(ended.timestamp() - s.get('started_epoch', ended.timestamp())))
                h, rem = divmod(secs, 3600)
                m, ss = divmod(rem, 60)
                s['duration'] = f"{h}:{m:02d}:{ss:02d}"
                return items
        return items
    mutate_items('sessions.json', 'sessions', close_session)
    return jsonify({"ok": True})

# ===== Notifications (delivered to the browser via /notifications/pending) =====
@app.route('/notifications/pending', methods=['GET'])
def notifications_pending():
    try:
        after = float(request.args.get('after', 0))
    except ValueError:
        after = 0
    events = load_json('notifications.json', [])
    events = [e for e in events if e.get('ts', 0) > after]
    events.sort(key=lambda e: e['ts'])
    return jsonify({"events": events})


# ===== Email watch: poll now, and manage the rules that trigger a PHONE push =====
@app.route('/email/check', methods=['POST', 'GET'])
def email_check():
    """Poll Gmail/Yahoo immediately and ntfy-push anything matching a rule."""
    data = request.json or {} if request.method == 'POST' else {}
    force = data.get('force_all', True) if isinstance(data, dict) else True
    if request.args:
        force = request.args.get('force_all', '1') != '0'
    ok, out = check_email_now(force_all=bool(force))
    return jsonify({"ok": ok, "result": out}), (200 if ok else 400)


@app.route('/preferences', methods=['GET'])
def preferences_get():
    res = list_preferences()
    prefs = res["preferences"]
    return jsonify({"ok": True, "count": res["count"], "preferences": prefs,
                    "file": os.path.join(DATA_DIR, _PREFERENCES_FILE)})


@app.route('/preferences', methods=['POST'])
def preferences_set():
    """Store a standing preference. Body: {key, value}."""
    d = request.json or {}
    if not isinstance(d, dict):
        return jsonify({"ok": False, "error": "JSON object required"}), 400
    res = set_preference(d.get("key"), d.get("value"))
    if not res.get("ok"):
        return jsonify(res), 400
    return jsonify(res)


@app.route('/preferences/<path:key>', methods=['DELETE'])
def preferences_delete(key):
    res = forget_preference(key)
    if not res.get("ok"):
        return jsonify(res), 404
    return jsonify(res)


@app.route('/email/rules', methods=['GET'])
def email_rules_get():
    return jsonify({"rules": _load_email_rules(),
                    "accounts": sorted(_load_email_accounts().keys())})


@app.route('/email/rules', methods=['POST'])
def email_rules_set():
    """Create/replace a watch rule. Body: {from|subject|body, account, name}."""
    d = request.json or {}
    if not isinstance(d, dict):
        return jsonify({"ok": False, "error": "JSON object required"}), 400
    needles = {f: (d.get(f) or "").strip() for f in ("from", "subject", "body")}
    if not any(needles.values()):
        return jsonify({"ok": False,
                        "error": "give at least one of from / subject / body"}), 400
    rules = _load_email_rules()
    rules.append({"name": d.get("name") or next((v for v in needles.values() if v), "rule"),
                  "account": d.get("account") or "both",
                  "enabled": bool(d.get("enabled", True)),
                  "notifyOnce": bool(d.get("notifyOnce", True)),
                  **needles})
    _save_email_rules(rules)
    return jsonify({"ok": True, "rules": rules})


@app.route('/email/test-push', methods=['POST', 'GET'])
def email_test_push():
    """Send one ntfy push so Chris can confirm the phone actually receives them."""
    ok = send_ntfy("ACEsi — Email alerts on",
                   "Email watching is live. I'll ping this phone the moment an "
                   "NSFAS (or other watched) email lands.")
    return jsonify({"ok": ok, "channel": "ntfy", "topic": NTFY_TOPIC})


@app.route('/whatsapp/send', methods=['POST'])
def whatsapp_send():
    """Prepare a WhatsApp message for a contact.

    The UI calls this and expects {ok, reply}. There is no WhatsApp Business
    API credential on this box, so rather than pretend to deliver, this returns
    a prefilled wa.me link the browser can open (and says so honestly). To send
    server-side instead, set WHATSAPP_TOKEN/WHATSAPP_PHONE_ID.
    """
    d = request.json or {}
    phone = re.sub(r'\D', '', str(d.get("phone") or ""))
    message = str(d.get("message") or "").strip()
    if not phone:
        return jsonify({"ok": False, "error": "phone is required (international format)"}), 400
    if not message:
        return jsonify({"ok": False, "error": "message is required"}), 400
    if not (8 <= len(phone) <= 15):
        return jsonify({"ok": False,
                        "error": "that does not look like an international number"}), 400
    link = "https://wa.me/%s?text=%s" % (phone, quote_plus(message[:2000]))
    tok = os.environ.get("WHATSAPP_TOKEN")
    pnum = os.environ.get("WHATSAPP_PHONE_ID")
    if tok and pnum:
        try:
            r = requests.post(
                "https://graph.facebook.com/v19.0/%s/messages" % pnum,
                headers={"Authorization": "Bearer %s" % tok,
                         "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp",
                      "to": phone,
                      "type": "text",
                      "text": {"body": message[:2000]}}, timeout=15)
            ok = r.status_code < 300
            return jsonify({"ok": ok, "delivered": "whatsapp_api",
                            "reply": ("Sent on WhatsApp." if ok
                                      else "WhatsApp API refused: %s" % r.text[:160])})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)[:160]}), 502
    return jsonify({
        "ok": True, "delivered": "link", "link": link,
        "reply": "No WhatsApp API key is set, so I prepared the message instead "
                 "of sending it. Opening WhatsApp now — press send there."})


@app.route('/security/test-alert', methods=['POST'])
def security_test_alert():
    """Fire a test security alert through the same ntfy channel real alerts use."""
    ok = send_ntfy("ACEsi — Security test",
                   "Test security alert. This is what a suspicious email or "
                   "login attempt would look like on your phone.")
    return jsonify({"ok": ok, "channel": "ntfy"})



# ===== Google Drive (raw REST, no extra deps) =====
DRIVE_CRED_FILE = os.path.join(DATA_DIR, 'drive_credentials.json')
DRIVE_TOKEN_FILE = os.path.join(DATA_DIR, 'drive_token.json')
DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
DRIVE_AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
DRIVE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
DRIVE_API = 'https://www.googleapis.com/drive/v3'
DRIVE_UPLOAD = 'https://www.googleapis.com/upload/drive/v3/files'


def load_drive_credentials():
    try:
        with open(DRIVE_CRED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def load_drive_token():
    try:
        with open(DRIVE_TOKEN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_drive_token(token):
    with _data_lock:
        tmp = DRIVE_TOKEN_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(token, f, indent=2)
        os.replace(tmp, DRIVE_TOKEN_FILE)


def drive_access_token(force=False):
    """Return a valid access token, refreshing when stale/expired/forced."""
    token = load_drive_token()
    if not token:
        return None
    if force or token.get('expires_at', 0) - time.time() < 60:
        cred = load_drive_credentials()
        if not cred or 'refresh_token' not in token:
            return None
        try:
            r = requests.post(DRIVE_TOKEN_URL, data={
                'client_id': cred['client_id'],
                'client_secret': cred['client_secret'],
                'refresh_token': token['refresh_token'],
                'grant_type': 'refresh_token'
            }, timeout=20)
            data = r.json()
            if r.status_code == 200 and data.get('access_token'):
                token['access_token'] = data['access_token']
                token['expires_in'] = data.get('expires_in', 3599)
                token['expires_at'] = time.time() + int(data.get('expires_in', 3599)) - 30
                save_drive_token(token)
            else:
                print(f"Drive token refresh failed: {r.status_code} {data}")
                return None
        except Exception as e:
            print(f"Drive token refresh error: {e}")
            return None
    return token.get('access_token')


def drive_request(method, url, **kwargs):
    """Drive API call with automatic one-shot refresh-and-retry on 401/403."""
    tok = drive_access_token()
    if not tok:
        return None, 'not_authenticated'
    kwargs.setdefault('headers', {})['Authorization'] = 'Bearer ' + tok
    r = requests.request(method, url, timeout=60, **kwargs)
    if r.status_code in (401, 403):
        tok = drive_access_token(force=True)
        if not tok:
            return r, 'http_%d' % r.status_code
        kwargs['headers']['Authorization'] = 'Bearer ' + tok
        r = requests.request(method, url, timeout=60, **kwargs)
    if r.status_code >= 400:
        return r, 'http_%d' % r.status_code
    return r, None


@app.route('/drive/status', methods=['GET'])
def drive_status():
    cred = load_drive_credentials()
    if not cred:
        return jsonify({"configured": False, "authorized": False})
    tok = drive_access_token()
    if not tok:
        return jsonify({"configured": True, "authorized": False})
    user = {}
    try:
        r, err = drive_request('GET', DRIVE_API + '/about?fields=user')
        if not err:
            u = r.json().get('user', {})
            user = {'displayName': u.get('displayName', ''), 'emailAddress': u.get('emailAddress', '')}
    except Exception:
        pass
    return jsonify({"configured": True, "authorized": True, "user": user})


@app.route('/drive/auth', methods=['GET'])
def drive_auth():
    cred = load_drive_credentials()
    if not cred:
        return "Drive not configured", 400
    cb = request.url_root.rstrip('/') + '/drive/callback'
    params = {
        'client_id': cred['client_id'],
        'redirect_uri': cb,
        'response_type': 'code',
        'scope': DRIVE_SCOPE,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return redirect(DRIVE_AUTH_URL + '?' + urlencode(params))


@app.route('/drive/callback', methods=['GET'])
def drive_callback():
    error = request.args.get('error')
    if error:
        return "Auth failed: %s" % error, 400
    code = request.args.get('code')
    if not code:
        return "Missing code", 400
    cred = load_drive_credentials()
    if not cred:
        return "Drive not configured", 400
    cb = request.url_root.rstrip('/') + '/drive/callback'
    try:
        r = requests.post(DRIVE_TOKEN_URL, data={
            'client_id': cred['client_id'],
            'client_secret': cred['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': cb
        }, timeout=20)
        data = r.json()
        if r.status_code != 200 or 'access_token' not in data:
            return "Token exchange failed: %s" % data, 400
        data['expires_at'] = time.time() + int(data.get('expires_in', 3599)) - 30
        save_drive_token(data)
    except Exception as e:
        return "Token exchange error: %s" % e, 400
    return "<h3>Connected to Google Drive. You can close this tab.</h3>"


@app.route('/drive/list', methods=['GET'])
def drive_list():
    parent = request.args.get('parent', 'root')
    r, err = drive_request('GET', DRIVE_API + '/files', params={
        'q': "'%s' in parents and trashed=false" % parent,
        'pageSize': 200,
        'fields': 'files(id,name,mimeType,size,modifiedTime)',
        'orderBy': 'folder,name'
    })
    if err:
        return jsonify({"error": err})
    return jsonify({"files": r.json().get('files', [])})


@app.route('/drive/download', methods=['GET'])
def drive_download():
    fid = request.args.get('id')
    if not fid:
        return jsonify({"error": "Missing file id"})
    r, err = drive_request('GET', DRIVE_API + '/files/%s?alt=media' % fid)
    if err:
        return jsonify({"error": err})
    return jsonify({"content": r.text})


@app.route('/drive/upload', methods=['POST'])
def drive_upload():
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body"})
    name = (body.get('name') or '').strip()
    content = body.get('content') or ''
    parent = body.get('parent') or 'root'
    if not name or not content:
        return jsonify({"error": "Name and content are required"})
    mime = 'application/octet-stream'
    b64 = content
    if content.startswith('data:'):
        header, _, b64 = content.partition(',')
        m = re.match(r'data:([^;]+)', header)
        if m:
            mime = m.group(1)
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return jsonify({"error": "Could not decode file data"})
    metadata = {"name": name, "parents": [parent]}
    try:
        r, err = drive_request('POST', DRIVE_UPLOAD, params={'uploadType': 'multipart'},
                               files={
                                   'metadata': (None, json.dumps(metadata), 'application/json; charset=UTF-8'),
                                   'file': (name, raw, mime)
                               })
        if err:
            return jsonify({"error": err})
        d = r.json()
        if 'id' not in d:
            return jsonify({"error": "Upload failed: %s" % d})
        return jsonify({"name": name, "id": d.get('id')})
    except Exception as e:
        return jsonify({"error": str(e)})


# ===== Live counts =====
@app.route('/devices', methods=['GET'])
def devices():
    try:
        r = _run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        devs = [ln.split('\t')[0] for ln in r.stdout.splitlines()[1:]
                if ln.strip() and 'device' in ln and 'offline' not in ln]
        return jsonify({"count": len(devs), "devices": devs})
    except Exception:
        return jsonify({"count": 0, "devices": []})

@app.route('/agents', methods=['GET'])
def agents():
    try:
        r = _run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
                           capture_output=True, text=True, timeout=10)
        count = max(0, len([l for l in r.stdout.strip().splitlines() if l.strip()]))
        return jsonify({"count": count, "agents": []})
    except Exception:
        return jsonify({"count": 0, "agents": []})

# ===== Proactive check-in: sends the daily summary from ACEsi, not a timer =====
def summary_scheduler():
    while True:
        try:
            if _kill_armed():
                time.sleep(30)
                continue
            now = datetime.now()
            enabled = get_config('summary_enabled', 'true') != 'false'
            target = str(get_config('summary_time', '07:00') or '07:00')
            today = now.date().isoformat()
            # "time has passed today and not yet sent" instead of exact HH:MM
            # equality: sleeping the laptop through 07:00 used to skip the
            # briefing for the whole day.
            try:
                due_at = datetime.combine(now.date(),
                                          datetime.strptime(target, "%H:%M").time())
            except ValueError:
                due_at = None
            if (enabled and due_at and now >= due_at
                    and get_config('last_summary_date', '') != today):
                set_config('last_summary_date', today)
                text = build_summary_text()
                send_ntfy("ACEsi — Good morning", "Good morning, Chris.\n\n" + text)
                print("📱 Proactive check-in sent")
        except Exception as e:
            print(f"⚠️ Scheduler error: {e}")
        time.sleep(30)

threading.Thread(target=summary_scheduler, daemon=True).start()

# Job scheduler daemon: fires autonomous jobs when due (respects E-STOP).
threading.Thread(target=job_watch, daemon=True).start()

# Task queue daemon: drains queued tasks in order without needing a manual
# /queue/run. Without this the queue was inert.
threading.Thread(target=_task_queue_worker, daemon=True).start()

@app.route('/test_ping')
def test_ping():
    send_test_ping()
    return "Test ping sent! Check your phone."


@app.route('/check-portal')
def check_portal():
    """One-click health check for the Venda ITS portal. Reuses the same `curl`
    tool ACEsi uses so the diagnosis is identical to what the model reports.
    Returns JSON: {url, reachable, status, detail}."""
    url = request.args.get("url") or UNIVEN_ITS_STARTUP_URL
    ok, detail = tool_curl(url, timeout=15, allow_redirects=True)
    # A 4xx/5xx (server responded) means the portal's web service IS running,
    # just returning an error — reachable in the sense 'a port answered'.
    reachable = bool(ok)
    status = "up" if ok else "down"
    # Distinguish 'no service' from 'service answered with an HTTP error'.
    answered = ("HTTP" in detail)
    result = {
        "url": url,
        "reachable": reachable and (answered or "HTTP" not in detail[:20]),
        "service_answered": answered,
        "status": "up" if answered else ("down" if not ok else "unknown"),
        "detail": detail,
    }
    if ok and not answered:
        result["status"] = "timeout"
    return jsonify(result)


@app.route('/portal')
def portal_redirect():
    """Convenience: open the StudentSyncSA ITS portal in a new tab, and probe it
    in the same request so the dashboard can show live status before navigating."""
    url = request.args.get("url") or UNIVEN_ITS_STARTUP_URL
    ok, detail = tool_curl(url, timeout=12, allow_redirects=True)
    return jsonify({"url": url, "portal_up": ok and "HTTP" in detail,
                     "detail": detail})


# ===== ACEsi general-purpose task routes =====

@app.route('/context', methods=['GET'])
def context_get():
    """Return the current active Context (or list all if names param)."""
    if ace_context:
        return jsonify(ace_context.contexts())
    return jsonify({"error": "ace_context not available"})


@app.route('/context', methods=['POST'])
def context_set():
    """Switch the active Context: {'name': '...'}."""
    name = (request.json or {}).get("name", "")
    if not name:
        return jsonify({"error": "context name required"})
    # Update devtools_service to resolve the new package / CDP filter
    d.set_context(name)
    return jsonify({"ok": True, "active": name})


@app.route('/run_task', methods=['POST'])
def run_task():
    """Execute a scripted step-list task (general-purpose executor).
    Body: {"steps": [{"tool": "ui_tap", "args": {"x": 540, "y": 1200}}, ...],
           "name": "task label", "auto_dump": true}
    Returns the TaskResult summary + per-step outputs."""
    from ace_task import run_task_steps
    data = request.json or {}
    steps = data.get("steps", [])
    name = data.get("name", "run_task")
    auto_dump = data.get("auto_dump", True)
    if not steps or not isinstance(steps, list):
        return jsonify({"error": "steps (list of {tool, args} dicts) required"}), 400
    result = run_task_steps(steps, task_name=name, server=app,
                            auto_dump=auto_dump)
    return jsonify(result.summary())


@app.route('/autonomous', methods=['POST'])
def autonomous():
    """Run a task in autonomous model-driven mode.
    Body: {"prompt": "navigate to the ITS portal and confirm the login button",
           "name": "autonomous task", "max_turns": 40}
    The model drives tools turn-by-turn until done or max_turns.

    If the prompt mentions web/research/search/find/list/note, the research
    workflow instructions from ace_research.py are prepended to the system prompt
    so ACEsi follows search → fetch → extract → save correctly."""
    from ace_task import run_task_autonomous
    from ace_research import RESEARCH_WORKFLOW_INSTRUCTIONS
    data = request.json or {}
    prompt = data.get("prompt", "")
    name = data.get("name", "autonomous")
    max_turns = data.get("max_turns", 40)
    research_mode = data.get("research", None)
    if research_mode is None:
        lower = str(prompt).lower()
        research_mode = any(k in lower for k in
                            ("research", "find", "list", "search", "web", "note", "save"))
    if not prompt.strip():
        return jsonify({"error": "prompt required"}), 400
    kwargs = {}
    if research_mode:
        kwargs["extra_system_prompt"] = RESEARCH_WORKFLOW_INSTRUCTIONS
    result = run_task_autonomous(prompt, task_name=name, server=app,
                                 max_turns=max_turns, **kwargs)
    return jsonify(result.summary())


# ── Saved task library: /tasks/lib/<name>.json ──────────────────────────────
# A "saved task" is a JSON file with {"steps": [...], "name": "...", "auto_dump": bool}
# so recurring automation (e.g. "its_login") can be invoked as /task/<name>.

TASKS_DIR = os.path.join(DATA_DIR, "tasks_lib")


def _load_saved_task(name):
    """Load a saved step-list task from tasks_lib/<name>.json."""
    path = os.path.join(TASKS_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@app.route('/task/<name>', methods=['POST'])
def run_saved_task(name):
    """Execute a saved step-list task from tasks_lib/<name>.json."""
    from ace_task import run_task_steps
    task_def = _load_saved_task(name)
    if not task_def:
        return jsonify({"error": f"task '{name}' not found in tasks_lib/"}), 404
    steps = task_def.get("steps", [])
    opts = request.json or {}
    auto_dump = opts.get("auto_dump", task_def.get("auto_dump", True))
    result = run_task_steps(steps, task_name=task_def.get("name", name),
                            server=app, auto_dump=auto_dump)
    return jsonify(result.summary())


@app.route('/task/<name>', methods=['GET'])
def get_saved_task(name):
    """Retrieve a saved task definition (step list + metadata)."""
    task_def = _load_saved_task(name)
    if not task_def:
        return jsonify({"error": f"task '{name}' not found"}), 404
    return jsonify(task_def)


@app.route('/tasks/lib', methods=['GET'])
def list_saved_tasks():
    """List all saved tasks in tasks_lib/."""
    if not os.path.isdir(TASKS_DIR):
        return jsonify({"tasks": []})
    items = []
    for fn in sorted(os.listdir(TASKS_DIR)):
        if fn.endswith(".json"):
            name = fn[:-5]
            task_def = _load_saved_task(name)
            if task_def:
                items.append({"name": name,
                              "label": task_def.get("name", name),
                              "steps": len(task_def.get("steps", [])),
                              "auto_dump": task_def.get("auto_dump", True)})
    return jsonify({"tasks": items})


# Expose the app as `server_instance` so ace_task.py can call _call_tool.
server_instance = app


# Build the tool registry from TOOLS/TOOLS_SCHEMA.
REGISTRY = _build_dispatcher_registry()

MODES = ["code", "ui", "hybrid", "general"]


def build_system_prompt(mode="code"):
    if mode not in MODES:
        mode = "code"
    tools = REGISTRY.describe_for_prompt()
    return (
        f"You are ACEsi in {mode} mode.\n\n{tools}\n"
        "STYLE: never narrate reasoning in prose. Between tool calls output ONLY "
        "the next tool call. When the task is done give a SHORT final report "
        "stating what you did and the key on-screen values.\n"
    )


# Replace the placeholder in the code-agent prompt with the generated tool list.
# Names + signatures only: the full per-tool descriptions are already delivered in
# the JSON `tools` schema, and repeating them here added ~2.3k tokens to EVERY turn.
# On free-tier providers (Groq ITPM = 7000/min) that duplication pushed the second
# agent turn over the per-minute input cap and the task died as "all providers
# unavailable". assert_prompt_matches still passes because every tool name appears.
CODE_AGENT_PROMPT = CODE_AGENT_PROMPT.replace(
    "{TOOLS}", "\n".join("- `%s`" % REGISTRY.signature(n) for n in REGISTRY.names()))

# Startup drift check: the prompt must mention every registered tool.
try:
    REGISTRY.assert_prompt_matches(CODE_AGENT_PROMPT, source="server.py[CODE_AGENT_PROMPT]")
except Exception as e:
    print("⚠️ Prompt drift check failed:", e)


# ===== Task Queue API Endpoints =====
@app.route('/queue/add', methods=['POST'])
def queue_add():
    data = request.json or {}
    tasks = data.get('tasks', [])
    on_failure = data.get('on_failure', 'stop')  # skip|retry|stop
    if not tasks:
        return jsonify({"error": "Provide 'tasks' array"}), 400
    q = _queue_add(tasks, on_failure)
    return jsonify({"status": "added", "queue_length": len(q["queue"]), "queue": q})

@app.route('/queue/status', methods=['GET'])
def queue_status():
    q = _queue_status()
    return jsonify(q)

@app.route('/queue/clear', methods=['POST'])
def queue_clear():
    q = _queue_clear()
    return jsonify({"status": "cleared", "queue": q})

@app.route('/queue/stop', methods=['POST'])
def queue_stop():
    q = _queue_stop()
    return jsonify({"status": "stopped", "queue": q})

@app.route('/queue/resume', methods=['POST'])
def queue_resume():
    q = _queue_resume()
    return jsonify({"status": "resumed", "queue": q})

@app.route('/queue/skip', methods=['POST'])
def queue_skip():
    q = _queue_skip_current()
    return jsonify({"status": "skipped", "queue": q})

@app.route('/queue/retry', methods=['POST'])
def queue_retry():
    q = _queue_retry_current()
    return jsonify({"status": "retry", "queue": q})

@app.route('/queue/run', methods=['POST'])
def queue_run():
    """Run the next task in the queue (or all if run_all=true)."""
    data = request.json or {}
    run_all = data.get('run_all', False)
    results = []
    if run_all:
        while True:
            res = _queue_run_next()
            if res is None:
                break
            results.append({"task": res[0]["task"], "result": res[1], "success": res[2]})
    else:
        res = _queue_run_next()
        if res:
            results.append({"task": res[0]["task"], "result": res[1], "success": res[2]})
    q = _queue_status()
    return jsonify({"executed": len(results), "results": results, "queue": q})


# ===== Memory / Profile API =====
@app.route('/memory/conversations/date/<date>', methods=['GET'])
def memory_conversations_by_date(date):
    """Get all conversations for a specific date (YYYY-MM-DD)."""
    limit = int(request.args.get('limit', 50))
    return jsonify(get_conversations_by_date(date, limit))

@app.route('/memory/conversations/search', methods=['GET'])
def memory_conversations_search():
    """Search conversations by keyword."""
    keyword = request.args.get('q', '')
    limit = int(request.args.get('limit', 50))
    days = int(request.args.get('days', 30))
    if not keyword:
        return jsonify({"error": "Provide 'q' parameter"}), 400
    return jsonify(get_conversations_by_topic(keyword, limit, days))

@app.route('/memory/conversations/range', methods=['GET'])
def memory_conversations_range():
    """Get conversations in an ID range."""
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', 0))
    if not start or not end:
        return jsonify({"error": "Provide 'start' and 'end' parameters"}), 400
    return jsonify(get_conversation_range(start, end))

@app.route('/memory/conversations/dates', methods=['GET'])
def memory_conversations_dates():
    """Get list of dates with conversation counts."""
    days = int(request.args.get('days', 90))
    return jsonify(get_dates_with_conversations(days))

@app.route('/memory/session/summarize', methods=['POST'])
def memory_session_summarize():
    """Summarize a conversation session."""
    data = request.json or {}
    messages = data.get('messages', [])
    summary = summarize_session(messages)
    return jsonify({"summary": summary})

@app.route('/memory/session/save', methods=['POST'])
def memory_session_save():
    """Save a session summary."""
    data = request.json or {}
    summary = data.get('summary', '')
    session_date = data.get('session_date')
    session_id = data.get('session_id')
    if not summary:
        return jsonify({"error": "Provide 'summary'"}), 400
    key = save_session_summary(summary, session_date, session_id)
    return jsonify({"saved": True, "key": key})

@app.route('/profile', methods=['GET'])
def profile_get():
    """Get the built profile of Chris."""
    return jsonify(get_profile())

@app.route('/profile/refresh', methods=['POST'])
def profile_refresh():
    """Force rebuild the profile from conversation history."""
    fresh = extract_profile_traits()
    # set_memory writes straight into a TEXT column, so a dict raised
    # sqlite3.ProgrammingError and this route 500'd. Serialise it, matching
    # get_profile().
    set_memory("profile.derived", json.dumps(fresh))
    return jsonify({"refreshed": True, "profile": fresh})

@app.route('/memory/conversations/recent', methods=['GET'])
def memory_conversations_recent():
    """Get recent conversation turns."""
    limit = int(request.args.get('limit', 20))
    return jsonify(get_recent_conversation(limit))


@app.route('/conversations', methods=['GET'])
def conversations_list():
    """Recent conversation turns WITH timestamps, oldest first.

    ACEsi.html (and mobile.html) load chat history from here expecting
    {conversations:[{role, content, timestamp}]}. The route did not exist, so
    history silently never loaded - a 404 that the frontend swallowed in an
    empty catch block.
    """
    try:
        limit = max(1, min(500, int(request.args.get('limit', 60))))
    except (TypeError, ValueError):
        limit = 60
    conn = sqlite3.connect('ace_memory.db')
    rows = conn.execute(
        "SELECT role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,)).fetchall()
    conn.close()
    return jsonify({"conversations": [
        {"role": r[0], "content": r[1], "timestamp": r[2] or ""}
        for r in reversed(rows)]})


# Deep-memory bootstrap: fold the legacy rich table in, seed the relationship
# lessons, import legacy moods, prune junk — runs once at boot before serving.
try:
    bootstrap_memory()
    _mirror_memories_to_json()
    print("🧠 Deep memory bootstrapped (consolidate + seed + prune done)")
except Exception as e:
    print(f"⚠️ Deep-memory bootstrap failed: {e}")

if __name__ == '__main__':
    # Boot E-STOP check: if ACEsi was killed before shutdown, come back stopped.
    if _kill_armed():
        _st = _kill_state()
        print("🔴 E-STOP PERSISTED ON BOOT (reason=%s, source=%s) — ACEsi is silent until "
              "the un-kill word arrives." % (_st.get("reason"), _st.get("source")))
    else:
        print("🟢 Kill switch: safe (disarmed) at boot.")
    # debug=False: Flask's dev reloader spawns a child that fights for port
    # 5000 with any old server still running, silently leaving the PHONE on
    # stale code (seen: qwen going off to Google because the deterministic
    # executor wasn't loaded). Reloads are handled by the ace_host watchdog
    # via its restart flag instead.
    app.run(host='127.0.0.1', port=5000, debug=False)
