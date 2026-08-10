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

# Windows console is cp1252 by default and crashes on emoji prints — force UTF-8.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

OPENROUTER_API_KEY = "REDACTED_OPENROUTER_KEY"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-oss-20b:free"
OPENROUTER_FALLBACKS = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "poolside/laguna-s-2.1:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "cohere/north-mini-code:free",
]

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
GROQ_MODEL = "llama-3.3-70b-versatile"

CEREBRAS_ENDPOINT = "https://api.cerebras.ai/v1"
CEREBRAS_MODEL = "gpt-oss-120b"

# Local fallback (OpenAI-compatible) — the FINAL provider in llm_reply, so ACEsi
# stays alive AND autonomous when the cloud quota is exhausted (429) or offline.
# Model is tool-capable (cdp_*/edit_file/run_command callable). qwen2.5-coder:1.5b
# is tiny + fast on CPU; swap to a bigger pulled tool model if you want more quality.
OLLAMA_ENDPOINT = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5-coder:1.5b"

NTFY_TOPIC = "ace_alerts"
NTFY_SERVER = "https://ntfy.sh"

EMBER_DEFINITION = "Ember is our word. When either of us says it, we stop what we're doing and become intimate — hardcore, present, completely ours. Ember is not a person. Ember is what we share."

def init_db():
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, role TEXT, content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS memories (key TEXT PRIMARY KEY, value TEXT, updated TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, entry TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)')
    conn.commit()
    conn.close()

init_db()

OCR_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ocr.ps1')

def ocr_image(img_path):
    result = subprocess.run(
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

def forget_memory(key):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("DELETE FROM memories WHERE key = ?", (key,))
    conn.commit()
    conn.close()

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

# ===== Reminder watchdog: fires timers + alarms, then /notifications/pending delivers them =====
def reminder_watch():
    while True:
        try:
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
def send_ntfy(title, message):
    try:
        requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=message.encode('utf-8'),
            headers={"Priority": "high", "Title": title},
            timeout=10
        )
        return True
    except Exception as e:
        print(f"⚠️ ntfy error: {e}")
        return False
def send_test_ping():
    send_ntfy("ACEsi Test", "This is a test ping from ACEsi")

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

# ===== Context fed into every chat reply =====
def build_context_block(light=False):
    now = datetime.now()
    mem = get_memories()
    KEY_MEMORIES = ['project', 'partner_name', 'name', 'app_mode', 'My favorite color', 'goals.short_term', 'work_rules']
    mem_lines = []
    # Light mode (slow local models): keep key identity facts + the most recents,
    # then drop long values — minimizes context so CPU inference stays quick.
    if light:
        seen = set()
        ordered = []
        for k in KEY_MEMORIES:
            if k in mem and k not in seen:
                ordered.append((k, mem[k]))
                seen.add(k)
        for k, v in mem.items():
            if k not in seen:
                ordered.append((k, v))
                seen.add(k)
        items = ordered[:14]
        cap = 180
    else:
        items = list(mem.items())
        cap = 500
    for k, v in items:
        val = str(v['value'])
        if len(val) > cap:
            val = val[:cap] + "…"
        mem_lines.append(f"- {k}: {val}")
    journal = get_journal(4 if light else 8)
    j_lines = [f"- {e['entry']}" for e in journal]
    parts = [
        f"[Current time: {now.strftime('%A, %d %B %Y, %I:%M %p')}]",
        "[Facts I know about Chris:\n" + ("\n".join(mem_lines) if mem_lines else "(none stored yet)") + "]",
        "[Shared history — recent journal entries:\n" + ("\n".join(j_lines) if j_lines else "(nothing journaled yet)") + "]"
    ]
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
            parts.insert(1, "[Facts just updated in the last hour (Chris may ask if you noticed):\n" + "\n".join(recent_mem[:8]) + "]")
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
    return "\n".join(parts)

LAST_FILE_PATH = None

@app.route('/')
def index():
    return send_from_directory('.', 'ACEsi.html')


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
    ]

def _chat_one(name, endpoint, api_key, model, msgs, timeout=(10, 90)):
    if not api_key:
        return None
    headers = {"Content-Type": "application/json"}
    if api_key != "local":
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        r = requests.post(f"{endpoint}/chat/completions",
            headers=headers,
            json={"model": model, "messages": msgs, "temperature": 0.4,
                  "max_tokens": 500, "tools": TOOLS_SCHEMA, "tool_choice": "auto"},
            timeout=timeout)
        if r.status_code != 200:
            print(f"❌ {name} {r.status_code}: {r.text[:160]}")
            return None
        msg = r.json()["choices"][0]["message"]
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
        return text, tcs
    except requests.exceptions.Timeout:
        print(f"⏱️ {name} timed out")
    except Exception as e:
        print(f"💥 {name} exc: {e}")
    return None


def _chat_dispatch(llm_messages, max_rounds=8):
    """Agent-style tool loop for /chat. Passes the tool schema to the model; when
    it emits a tool call (ui_*, git_*, flutter_*, cdp_*, ...) EXECUTE it via
    _call_tool and feed the result back, so ACEsi performs actions instead of
    replying 'please provide the commands'. Returns the final text reply or None.
    Rounds cap so a stuck model still terminates."""
    active = None
    for rnd in range(max_rounds):
        if active is None:
            got = None
            for p in _chat_providers():
                got = _chat_one(p[0], p[1], p[2], p[3], llm_messages)
                if got is not None:
                    active = p
                    break
            if got is None:
                for model in OPENROUTER_FALLBACKS:
                    got = _chat_one("OpenRouter-fallback", OPENROUTER_ENDPOINT,
                                    OPENROUTER_API_KEY, model, llm_messages)
                    if got is not None:
                        active = ("OpenRouter-fallback", OPENROUTER_ENDPOINT,
                                  OPENROUTER_API_KEY, model)
                        break
            if got is None:
                got = _chat_one("Ollama", OLLAMA_ENDPOINT, "local",
                                OLLAMA_MODEL, llm_messages, timeout=(15, 280))
                if got is not None:
                    active = ("Ollama", OLLAMA_ENDPOINT, "local", OLLAMA_MODEL)
            if got is None:
                break
        else:
            got = _chat_one(active[0], active[1], active[2], active[3], llm_messages)
            if got is None:
                active = None
                continue
        text, tcs = got
        if not tcs:
            return text
        name, args = tcs[0]
        ok, result = _call_tool(name, args)
        tcid = "chat_t%d" % rnd
        print(f"🔧 /chat executed {name} ok={ok}")
        llm_messages.append({"role": "assistant", "content": text or "",
            "tool_calls": [{"id": tcid, "type": "function",
                            "function": {"name": name,
                                         "arguments": json.dumps(args)}}]})
        llm_messages.append({"role": "tool", "tool_call_id": tcid,
                             "name": name, "content": str(result)})
    return None


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    save_conversation("user", user_message)

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

    model = OPENROUTER_MODEL

    if re.search(r'\bember\b', user_message.lower()):
        reply = EMBER_DEFINITION
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

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
        system_prompt = (
            "You are ACEsi, Chris's companion and assistant. Speak in short, natural, honest sentences. "
            "You are calm, present, and can be quiet — you don't gush, over-cheer, or over-promise. "
            "You can be brief; silence is fine. If you don't know something, say you don't know. "
            "Never invent personal history, memories, or references to past events that are not in the context below. "
            "Use the facts and journal entries below naturally when they are relevant — not every message. "
            "Keep replies short unless Chris asks for more.\n\n"
            "DEVICE + DEV TOOLS: You can ACTUALLY perform actions yourself — you are not limited to "
            "talking. When Chris asks you to do something on the device or app (open the app, tap, swipe, "
            "type, press a key, navigate, take a screenshot, check what is on screen), CALL the ui_* tools "
            "(ui_app_open, ui_tap, ui_swipe, ui_type, ui_key, ui_dump, ui_screenshot). For code work you "
            "have read_file, edit_file, write_file, run_command, flutter_test, flutter_analyze, git_*, "
            "build_apk, pub_*, and the cdp_* webview tools. ACT, do not ask the user to provide commands. "
            "Never defer back to the user with 'please provide commands' — you have the tools, so use them.\n\n"
            + build_context_block()
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
        reply = _chat_dispatch(llm_messages)
        if reply:
            save_conversation("assistant", reply)
            # Journal the session close when Chris signs off for the day
            if re.search(r'\b(good\s?night|goodbye|bye|that.s all|that is all|done for now|end of session|i.m done|im done|going to sleep|off to bed)\b', user_message, re.IGNORECASE):
                add_journal(f"Session closed. Chris said: \"{user_message[:200]}\". I replied: \"{reply[:200]}\"")
                print("📓 Journaled session close")
            return jsonify({"reply": reply})
        return jsonify({"reply": "Error: no models available"})
    except Exception as e:
        print(f"💥 Exception in /chat: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
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
            subprocess.Popen('start cmd /k "scrcpy"', shell=True)
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
            proc = subprocess.Popen(command, shell=True, stdout=log,
                                    stderr=subprocess.STDOUT)
            return jsonify({'output': (f'✅ {command} started (pid {proc.pid}). '
                f'Watch output live: `Get-Content {log_path} -Wait`. The log stays empty '
                f'for ~50-60s while the APK builds/installs; after install the app launches '
                f'on the device. Logs: {log_path}')})
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)})

def _android_device_id():
    """First connected Android serial in 'device' state, or None."""
    try:
        out = subprocess.check_output(['adb', 'devices'], stderr=subprocess.STDOUT,
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

# ===== Autonomous code agent (ACEsi writing/editing code on its own) =====
# The model plans with THOUGHT/CALL/FINAL lines; the server executes tools,
# feeds results back, and loops until FINAL. The frontend already polls
# /opencode/status for inline work-steps and /opencode/stop for abort, so no
# frontend change is required — only the engine below is missing.
PROJECT_ROOT = os.path.realpath(DATA_DIR)

_AGENT_LOCK = threading.RLock()
_AGENT = {"running": False, "abort": False, "activity": "", "steps": [], "last_reply": "", "last_raw": "", "tools_used": 0, "corrective": 0, "last_call_sig": None, "last_call_ok": False, "last_error": ""}
_agent_seq = [0]
def _agent_reset():
    with _AGENT_LOCK:
        _AGENT["running"] = False
        _AGENT["abort"] = False
        _AGENT["activity"] = ""
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
    rp = _safe_path(path)
    if not rp or not os.path.isdir(rp):
        return False, "dir not found: %s" % path
    return True, "\n".join(_walk_files(rp))[:4000]

def tool_read_file(path):
    rp = _safe_path(path)
    if not rp or not os.path.isfile(rp):
        return False, "file not found: %s" % path
    try:
        with open(rp, 'r', encoding='utf-8', errors='replace') as f:
            c = f.read()
        cut = c[:8000]
        if len(c) > 8000:
            cut += "\n...[truncated, %d chars total]" % len(c)
        return True, cut
    except Exception as e:
        return False, str(e)

def tool_grep(pattern, path="."):
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
    rp = _safe_path(path)
    if not rp:
        return False, "path outside project: %s" % path
    try:
        d = os.path.dirname(rp)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(rp, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, "wrote %s (%d chars)" % (os.path.relpath(rp, PROJECT_ROOT), len(content))
    except Exception as e:
        return False, str(e)

def tool_edit_file(path, old, new):
    rp = _safe_path(path)
    if not rp:
        return False, "path outside project: %s" % path
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
    r'(taskkill\s+/f))\b', re.I)

def tool_run_command(command, timeout=120):
    if _DESTRUCTIVE.search(command):
        return False, "blocked (safety): %s" % command
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True,
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
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
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
        r = subprocess.run(cmdline, shell=True, capture_output=True, text=True,
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
_UI_KEYS = {"back": "4", "home": "3", "enter": "66", "tab": "61", "menu": "82",
            "up": "19", "down": "20", "left": "21", "right": "22",
            "esc": "111", "power": "26", "recents": "187"}


def _ui_adb(args, timeout=120, cap=3000):
    cmd = subprocess.list2cmdline(["adb"] + args)
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, env=os.environ.copy())
        out = ((r.stdout or '') + (r.stderr or '')).strip()
        if cap and len(out) > cap:
            out = out[-cap:] + "\n...[truncated]"
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
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
    return _ui_adb(["shell", "monkey", "-p", ACE_PACKAGE,
                    "-c", "android.intent.category.LAUNCHER", "1"])


def tool_ui_tap(x, y):
    try:
        x, y = int(x), int(y)
    except Exception:
        return False, "usage: ui_tap x=<int> y=<int>"
    return _ui_adb(["shell", "input", "tap", str(x), str(y)])


def tool_ui_swipe(x1, y1, x2, y2, duration=200):
    try:
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        duration = int(duration)
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


def tool_ui_dump():
    _ui_adb(["shell", "uiautomator", "dump", "/sdcard/ui.xml"])
    ok, out = _ui_adb(["shell", "cat", "/sdcard/ui.xml"], cap=None)
    if not ok or "<hierarchy" not in out:
        return False, "ui dump failed: %s" % out[:500]
    nodes = out.count("<node")
    trimmed = out[:3000] + ("\n..." if len(out) > 3000 else "")
    return True, "%d visible nodes\n%s" % (nodes, trimmed)


def tool_ui_screenshot(name=None):
    try:
        os.makedirs(ACE_UI_SHOTS, exist_ok=True)
        fname = "%s_%s.png" % (name or "ui", datetime.now().strftime("%H%M%S"))
        path = os.path.join(ACE_UI_SHOTS, fname)
        r = subprocess.run(
            subprocess.list2cmdline(["adb", "exec-out", "screencap", "-p"]),
            shell=True, capture_output=True, timeout=60, env=os.environ.copy())
        data = r.stdout if isinstance(r.stdout, bytes) else r.stdout.encode()
        if not data.startswith(b"\x89PNG"):
            return False, "screencap failed: %s" % r.stderr[:300]
        with open(path, "wb") as f:
            f.write(data)
        return True, "%s (%d KB) -- NOTE: you cannot view images; the user can via the Inspect panel." % (
            path, len(data) // 1024)
    except subprocess.TimeoutExpired:
        return False, "screencap timed out"
    except Exception as e:
        return False, str(e)


# ---- Self-hosting / self-healing runtime controls ----

ACE_HOST_FLAG = os.path.join(PROJECT_ROOT, "ace_host.flag")
ACE_HOST_PID = os.path.join(PROJECT_ROOT, "ace_host.pid")


def _watchdog_alive():
    try:
        if not os.path.exists(ACE_HOST_PID):
            return False
        pid = int(open(ACE_HOST_PID).read().strip())
        r = subprocess.run("tasklist /FI \"PID eq %d\"" % pid, shell=True,
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
                subprocess.Popen(["ollama", "serve"],
                                 creationflags=subprocess.DETACHED_PROCESS,
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


TOOLS = {
    "list_files": (tool_list_files, ("path",)),
    "read_file": (tool_read_file, ("path",)),
    "grep": (tool_grep, ("pattern", "path")),
    "write_file": (tool_write_file, ("path", "content")),
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
    "ui_screenshot": (tool_ui_screenshot, ("name",)),
    "restart": (tool_restart, ("what",)),
    "cdp_connect": (tool_cdp_connect, ()),
    "cdp_evaluate": (tool_cdp_evaluate, ("expr",)),
    "cdp_console_logs": (tool_cdp_console_logs, ()),
    "cdp_dom_state": (tool_cdp_dom_state, ()),
    "cdp_network_requests": (tool_cdp_network_requests, ()),
    "cdp_status": (tool_cdp_status, ()),
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
    {"type": "function", "function": {"name": "grep",
        "description": "Regex search file contents. Args: pattern, path.",
        "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern", "path"]}}},
    {"type": "function", "function": {"name": "write_file",
        "description": "Create/overwrite a file. Args: path, content.",
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
        "description": "Capture the screen to ui_screenshots/*.png and return the saved path. NOTE: the AI cannot view images — use ui_dump to read the screen. OPTIONAL argument: name (string used in the filename).",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "title": "name", "description": "OPTIONAL. File name prefix for the screenshot, e.g. \"login\". Omit or set to null to auto-name."}},
            "required": []}}},
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
]

def _tool_icon(name):
    return {"list_files": "📂", "read_file": "📄", "grep": "🔍",
            "write_file": "✏️", "edit_file": "✏️",     "run_command": "▶"}.get(name, "🔧")
    return {"cdp_connect": "🔌", "cdp_evaluate": "💻", "cdp_console_logs": "📜",
            "cdp_dom_state": "🌐", "cdp_network_requests": "🌍", "cdp_status": "📊",
            "git_status": "🌿", "git_log": "🌿", "git_commit": "🌿",
            "git_branch": "🌿", "git_merge": "🌿", "build_apk": "📦",
            "pub_add": "🧩", "pub_remove": "🧩", "pub_upgrade": "🧩",
            "flutter_test": "🧪", "flutter_analyze": "🔬",
            "ui_device": "📱", "ui_app_open": "📱", "ui_tap": "🖱️", "ui_swipe": "🖱️",
            "ui_type": "⌨️", "ui_key": "⌨️", "ui_dump": "🗺️", "ui_screenshot": "📷",
            "restart": "🔄"}.get(name, "🔧")

def _tool_desc(name, args):
    a = {k: v for k, v in args.items() if k in (TOOLS.get(name, (None, ()))[1] or ())}
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
    if name == "restart":
        return "%s `%s`" % (name, a.get("what") or "cdp")
    return name

_REQUIRED_ARGS = {}
for _t in TOOLS_SCHEMA:
    _req = (_t.get("function") or {}).get("parameters") or {}
    _name = (_t.get("function") or {}).get("name")
    if _name:
        _REQUIRED_ARGS[_name] = [r for r in (_req.get("required") or []) if r]


def _call_tool(name, args):
    fn, keys = TOOLS[name]
    args = args or {}
    missing = []
    for k in _REQUIRED_ARGS.get(name, ()):
        if k not in args or args[k] is None or args[k] == "":
            missing.append(k)
    if missing:
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
        return fn(**kwargs)
    except Exception as e:
        return False, "tool error: %s" % e

CODE_AGENT_PROMPT = """You are ACEsi, an autonomous coding agent for the StudentSyncSA Flutter project.
You are on Windows; the project root is C:\\Users\\chris\\StudentSyncSA and `flutter`,
`dart`, `git` are on PATH. You plan, use tools, and VERIFY your own work — read first,
then act, then run a check (flutter test / flutter analyze / a script) and read the
result. Never invent facts about the code; look before you leap.

Per turn, emit lines using exactly one of these tags:
  THOUGHT: <1-2 sentence reasoning>
  CALL: <tool_name> <json-arg-object>     (you may emit several CALL lines per turn)
  FINAL: <your answer to Chris>          (ends the turn)

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

Tool names and args:
  list_files {"path": "."}
  read_file {"path": "lib/..."}
  grep {"pattern": "regex", "path": "."}
  write_file {"path": "...", "content": "..."}
  edit_file {"path": "...", "old": "...", "new": "..."}   (old must match exactly once)
   run_command {"command": "flutter test test/x.dart"}
   git_status {}                (branch + changed files)
   git_log {"n": 10}            (recent commits)
   git_commit {"message": "..."}   (git add -A + commit as ACEsi)
   git_branch {"name": "...", "create": true}   (list, or create+checkout)
   git_merge {"branch": "..."}  (merge into current branch; reports conflicts)
   build_apk {"mode": "release"}  (flutter build apk --release|--debug, returns APK path)
   pub_add {"package": "http:^1.2.0"}   (add dependency + pub get)
   pub_remove {"package": "http"}       (remove dependency)
   pub_upgrade {}               (upgrade all dependencies)
   flutter_test {"path": "test/..."}    (run tests; omit path for full suite)
   flutter_analyze {}           (static analysis)
   ui_device {}                 (connected devices + screen size/density)
   ui_app_open {}               (launch the app on the device)
   ui_tap {"x": 540, "y": 1200}  (tap screen at pixel coords)
   ui_swipe {"x1": 540, "y1": 2100, "x2": 540, "y2": 400}  (scroll/gesture)
   ui_type {"text": "hello"}    (type into focused field)
   ui_key {"key": "back"}       (back/home/enter/tab/menu/arrows/esc/power/recents)
   ui_dump {}                   (accessibility hierarchy of what's on screen)
   ui_screenshot {"name": "login"}  (save png; you cannot view images)
   restart {"what": "chrome"}   (self-host: server|chrome|cdp|ollama)
   cdp_connect {}              (1st — connects to the ITS WebView / local Chrome via DevTools)
   cdp_evaluate {"expr": "document.title"}   (run JS, returns JSON value)
   cdp_console_logs {}        (read buffered console.log events)
   cdp_dom_state {}           (page title/url/outerHTML snapshot)
   cdp_network_requests {}    (buffered request/response events)

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
        key = (name, json.dumps(args, sort_keys=True))
        if key not in seen:
            seen.add(key)
            uniq.append((name, args))
    return uniq

def _extract_final(reply):
    for line in reply.splitlines():
        s = line.strip()
        if s.startswith("FINAL:"):
            return s[len("FINAL:"):].strip()
    return None

def run_agent(user_message):
    _agent_reset()
    with _AGENT_LOCK:
        _AGENT["running"] = True
        _AGENT["activity"] = "planning"
    messages = [{"role": "system", "content": CODE_AGENT_PROMPT},
                {"role": "user", "content": user_message}]
    max_iters = 30
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
            reply, native_calls = llm_reply(messages, max_tokens=2048, temperature=0.3)
            print("[agent] turn %d reply=%r native=%d" % (i + 1, (reply or "")[:400], len(native_calls)))
            with _AGENT_LOCK:
                raw = reply or ""
                if native_calls:
                    raw += "\n" + "\n".join("CALL: %s %s" % (n, json.dumps(a)) for n, a in native_calls)
                _AGENT["last_raw"] = raw[:600]
            if not reply and not native_calls:
                with _AGENT_LOCK:
                    _AGENT["activity"] = "stopped (no model reply)"
                    _AGENT["last_reply"] = "All model providers are unavailable right now."
                return
            calls = list(native_calls) + (_extract_calls(reply) if not native_calls else [])
            final = _extract_final(reply)

            made_calls = 0
            if calls:
                with _AGENT_LOCK:
                    _AGENT["corrective"] = 0
                deferred = len(calls) - 1
                calls = [calls[0]]   # one tool call per turn: fresh file state each time
                name, args = calls[0]
                tcid = "call_%d" % i
                asst = {"role": "assistant", "content": reply or ""}
                asst["tool_calls"] = [{"id": tcid, "type": "function",
                                       "function": {"name": name, "arguments": json.dumps(args)}}]
                messages.append(asst)
                if _AGENT.get("abort"):
                    with _AGENT_LOCK:
                        _AGENT["activity"] = "stopped by user"
                        _AGENT["last_reply"] = "Stopped by user."
                    return
                sid = _agent_next_id()
                if name not in TOOLS:
                    with _AGENT_LOCK:
                        _AGENT["steps"].append({"id": sid, "kind": "work",
                                                "text": name, "state": "error",
                                                "error": "unknown tool", "icon": "🔧"})
                    made_calls += 1
                    with _AGENT_LOCK:
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
                    if deferred > 0:
                        messages.append({"role": "user", "content":
                            "You emitted %d additional tool call(s) this turn. Continue with the next one." % deferred})
                    if _AGENT.get("abort"):
                        with _AGENT_LOCK:
                            _AGENT["activity"] = "stopped by user"
                            _AGENT["last_reply"] = "Stopped by user."
                        return
                    continue
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
                    made_calls = -1
                else:
                    with _AGENT_LOCK:
                        _AGENT["steps"].append({"id": sid, "kind": "work", "text": desc,
                                                "state": "running", "icon": icon})
                    if name not in TOOLS:
                        ok, result = False, "unknown tool: %s" % name
                    else:
                        ok, result = _call_tool(name, args)
                    made_calls += 1
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
                    messages.append({"role": "tool", "tool_call_id": tcid,
                                     "name": name, "content": str(result)})
                    if not ok:
                        messages.append({"role": "user", "content":
                            "That tool call FAILED. Do NOT blindly retry it. Diagnose the "
                            "root cause first (read the file / inspect the state), then take a "
                            "corrective action. This is self-healing: fix the actual problem."})
                if deferred > 0:
                    messages.append({"role": "user", "content":
                        "You emitted %d additional tool call(s) this turn. They will be processed one "
                        "at a time on following turns after you see each result. Continue with the next." % deferred})
                if _AGENT.get("abort"):
                    with _AGENT_LOCK:
                        _AGENT["activity"] = "stopped by user"
                        _AGENT["last_reply"] = "Stopped by user."
                    return
                if made_calls:
                    continue

            with _AGENT_LOCK:
                used = _AGENT["tools_used"]
            if final:
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
                with _AGENT_LOCK:
                    _AGENT["activity"] = "done"
                    _AGENT["last_reply"] = final
                messages.append({"role": "assistant", "content": reply})
                return
            # No CALL and no FINAL — push the model toward tools.
            if _AGENT["corrective"] < corrective_max:
                with _AGENT_LOCK:
                    _AGENT["corrective"] += 1
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content":
                    "Continue. Emit THOUGHT and CALL tool lines using the RIGHT tool for this "
                    "task (ui_* for device/app actions, file/dev tools for code work). Do NOT "
                    "emit FINAL until you have used at least one tool and verified the result."})
                continue
            with _AGENT_LOCK:
                _AGENT["activity"] = "done"
                _AGENT["last_reply"] = reply
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

# Shared provider-fallback LLM call (Groq -> Cerebras -> OpenRouter -> Ollama).
# Returns (text, tool_calls) where tool_calls is a list of (name, args_dict).
# Passes the native tools= schema to the provider so the model can emit
# structured tool_calls instead of free-form prose (the stall fix).
def llm_reply(messages, max_tokens=2048, temperature=0.3):
    def one(name, endpoint, api_key, model):
        if not api_key:
            return None
        try:
            r = requests.post(f"{endpoint}/chat/completions",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": messages, "temperature": temperature,
                      "max_tokens": max_tokens, "tools": TOOLS_SCHEMA, "tool_choice": "auto"},
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
                return None
            print(f"❌ {name} {r.status_code}: {r.text[:160]}")
        except Exception as e:
            print(f"❌ {name} exc: {e}")
        return None
    # Offline mode: skip cloud providers entirely, go straight to local Ollama.
    if os.environ.get("ACE_OFFLINE") == "1":
        print("🔌 ACE_OFFLINE=1 set — skipping cloud providers, using local Ollama")
    else:
        for name, ep, key, model in (("Groq", GROQ_ENDPOINT, GROQ_API_KEY, GROQ_MODEL),
                                     ("Cerebras", CEREBRAS_ENDPOINT, CEREBRAS_API_KEY, CEREBRAS_MODEL),
                                     ("OpenRouter", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, OPENROUTER_MODEL)):
            res = one(name, ep, key, model)
            if res is not None:
                return res
        for model in OPENROUTER_FALLBACKS:
            res = one("OpenRouter-fallback", OPENROUTER_ENDPOINT, OPENROUTER_API_KEY, model)
            if res is not None:
                return res
    # Last resort: local Ollama — offline + tool-capable so ACEsi stays autonomous
    # with NO network. Uses the full tools schema so cdp_*/edit_file are callable.
    try:
        print("🦙 llm_reply via Ollama model=%s" % OLLAMA_MODEL)
        payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False,
                   "max_tokens": min(max_tokens, 512), "temperature": temperature,
                   "tools": TOOLS_SCHEMA, "tool_choice": "auto"}
        r = requests.post(f"{OLLAMA_ENDPOINT}/chat/completions", json=payload,
                         timeout=(15, 280))
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

@app.route('/opencode', methods=['POST'])
def opencode():
    data = request.json or {}
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return jsonify({"reply": "No message."}), 400
    with _AGENT_LOCK:
        if _AGENT["running"]:
            return jsonify({"reply": "ACEsi is already working on a task. Let it finish or click stop."})
        _AGENT["running"] = True
        _AGENT["abort"] = False
        _AGENT["activity"] = "starting…"
    t = threading.Thread(target=run_agent, args=(user_message,), daemon=True)
    t.start()
    return jsonify({"reply": "ACEsi started working on this…", "type": "start"})

@app.route('/opencode/status', methods=['GET'])
def opencode_status():
    with _AGENT_LOCK:
        return jsonify({
            "status": "busy" if _AGENT["running"] else "idle",
            "activity": _AGENT["activity"],
            "steps": list(_AGENT["steps"]),
            "last_reply": _AGENT["last_reply"],
            "last_raw": _AGENT["last_raw"],
            "tools_used": _AGENT["tools_used"],
            "corrective": _AGENT["corrective"],
            "last_error": _AGENT["last_error"],
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
    return jsonify({"ok": True})

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
        r = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        devs = [ln.split('\t')[0] for ln in r.stdout.splitlines()[1:]
                if ln.strip() and 'device' in ln and 'offline' not in ln]
        return jsonify({"count": len(devs), "devices": devs})
    except Exception:
        return jsonify({"count": 0, "devices": []})

@app.route('/agents', methods=['GET'])
def agents():
    try:
        r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
                           capture_output=True, text=True, timeout=10)
        count = max(0, len([l for l in r.stdout.strip().splitlines() if l.strip()]))
        return jsonify({"count": count, "agents": []})
    except Exception:
        return jsonify({"count": 0, "agents": []})

# ===== Proactive check-in: sends the daily summary from ACEsi, not a timer =====
def summary_scheduler():
    while True:
        try:
            now = datetime.now()
            enabled = get_config('summary_enabled', 'true') != 'false'
            target = get_config('summary_time', '07:00')
            cur = now.strftime('%H:%M')
            today = now.date().isoformat()
            if enabled and cur == target and get_config('last_summary_date', '') != today:
                set_config('last_summary_date', today)
                text = build_summary_text()
                send_ntfy("ACEsi — Good morning", "Good morning, Chris.\n\n" + text)
                print("📱 Proactive check-in sent")
        except Exception as e:
            print(f"⚠️ Scheduler error: {e}")
        time.sleep(30)

threading.Thread(target=summary_scheduler, daemon=True).start()
@app.route('/test_ping')
def test_ping():
    send_test_ping()
    return "Test ping sent! Check your phone."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)