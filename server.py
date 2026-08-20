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
OLLAMA_MODEL = "qwen2.5:7b"
# /chat dispatch prefers the much-faster 3b tool model on this CPU-only box;
# 7b costs ~80s per round vs ~20-40s for 3b. Quality is slightly lower but the
# dispatch loop + auto-dump makes it work. llm_reply (opencode path) keeps 7b.
OLLAMA_CHAT_MODEL = "qwen2.5:3b"

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

# This server runs DETACHED (no console window) under the ace_host watchdog.
# Any child subprocess that doesn't get CREATE_NO_WINDOW spawns a NEW visible
# console — a black window that flashes and vanishes, seen every time ACEsi
# loads a page that runs /devices or /agents. All subprocess calls go through
# these helpers so children never pop a window.
_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def _run(*args, **kw):
    kw.setdefault("creationflags", _NO_WINDOW)
    return subprocess.run(*args, **kw)


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
    body = {"model": model, "messages": msgs, "temperature": 0.4,
            "max_tokens": 500, "tools": tools_schema, "tool_choice": tool_choice}
    try:
        r = requests.post(f"{endpoint}/chat/completions",
            headers=headers,
            json=body,
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
            sys_ = {"role": "system", "content": OLLAMA_SYS_PROMPT}
        elif role == "user" and first_user is None and "SCREEN STATE" not in str(m.get("content", "")):
            if "You only described" not in str(m.get("content", "")) and \
               "I detected Chrome" not in str(m.get("content", "")) and \
               "SCREEN STATE" not in str(m.get("content", "")):
                first_user = m
        elif role in ("user", "assistant", "tool"):
            tail.append(m)
    return ([m for m in (sys_, first_user) if m] + tail[-3:]) if sys_ else (
        [m for m in (first_user,) if m] + tail[-3:])


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
        if is_ollama:
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


def _chat_dispatch(llm_messages, max_rounds=20, user_message=""):
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
    # Ollama uses the COMPACT schema (prompt-size critical on this CPU); cloud
    # providers get the FULL schema restricted to the active domain only.
    ollama_domain_schema = _filter_tools_schema(OLLAMA_TOOLS_SCHEMA, allowed_names)
    full_domain_schema = _filter_tools_schema(TOOLS_SCHEMA, allowed_names)

    with _AGENT_LOCK:
        _AGENT["running"] = True
        _AGENT["abort"] = False
        _AGENT["activity"] = "planning"
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
                tc = "required" if (_ui_task(user_message) and (not names or not last_had_tools)) else "auto"
                for p in _chat_providers():
                    got = _chat_one(p[0], p[1], p[2], p[3], llm_messages,
                                     tools_schema=full_domain_schema, tool_choice=tc)
                    if got is not None:
                        active = p
                        break
                if got is None:
                    for model in OPENROUTER_FALLBACKS:
                        got = _chat_one("OpenRouter-fallback", OPENROUTER_ENDPOINT,
                                        OPENROUTER_API_KEY, model, llm_messages,
                                        tools_schema=full_domain_schema, tool_choice=tc)
                        if got is not None:
                            active = ("OpenRouter-fallback", OPENROUTER_ENDPOINT,
                                      OPENROUTER_API_KEY, model)
                            break
                if got is None:
                    # Ollama warm-up probe first: cheap tiny call that forces the
                    # model to LOAD (with keep_alive persisted in Ollama) so the
                    # heavy first round reuses the loaded model instead of eating
                    # the whole timeout on a cold swap. MUST use the same /v1
                    # endpoint with the same options as the real call — changing
                    # num_ctx across calls reloads the model every round.
                    try:
                        _chat_one("Ollama", OLLAMA_ENDPOINT, "local",
                                  OLLAMA_CHAT_MODEL,
                                  [{"role": "user", "content": "ok"}],
                                  timeout=(15, 120),
                                  tools_schema=OLLAMA_TOOLS_SCHEMA)
                    except Exception:
                        pass
                    got = _chat_one("Ollama", OLLAMA_ENDPOINT, "local",
                                    OLLAMA_CHAT_MODEL, _ollama_local_messages(llm_messages),
                                    timeout=(15, 180),
                                    tools_schema=ollama_domain_schema, tool_choice=tc)
                    # Apply the same compact schema/messages to FOLLOW-UP rounds
                    # (active[3]==OLLAMA_CHAT_MODEL identifies the local model).
                    if got is not None:
                        active = ("Ollama", OLLAMA_ENDPOINT, "local", OLLAMA_CHAT_MODEL,
                                  "compact")
                if got is None:
                    break
            else:
                tc = "required" if (_ui_task(user_message) and (not names or not last_had_tools)) else "auto"
                if len(active) > 4 and active[4] == "compact":
                    got = _chat_one(active[0], active[1], active[2], active[3],
                                    _ollama_local_messages(llm_messages), timeout=(15, 180),
                                    tools_schema=ollama_domain_schema, tool_choice=tc)
                else:
                    got = _chat_one(active[0], active[1], active[2], active[3],
                                    llm_messages, tools_schema=ollama_domain_schema,
                                    tool_choice=tc)
                if got is None:
                    active = None
                    continue
            with _AGENT_LOCK:
                _AGENT["activity"] = "thinking (%d/%d)" % (rnd + 1, max_rounds)
            text, tcs = got
            if text and text.strip():
                last_text = text.strip()[:2000]
            # Small/prose-capable providers (Ollama qwen2.5) sometimes write the tool
            # call in prose ("CALL: ui_tap {...}" / fenced JSON) instead of native
            # tool_calls. Accept those too, exactly like run_agent's _extract_calls.
            if not tcs:
                tcs = _extract_calls(text)
            if not tcs:
                last_had_tools = False
                nav_push = _nav_gate(user_message, names)
                if nav_push:
                    llm_messages.append({"role": "user", "content": nav_push})
                    active = None
                    dead_rounds += 1
                    if dead_rounds >= 4:
                        with _AGENT_LOCK:
                            _AGENT["activity"] = "stopped (no tool calls)"
                        break
                    continue
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
                    with _AGENT_LOCK:
                        _AGENT["last_reply"] = _terse_reply(text or "")
                    return _terse_reply(text or "")
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
            llm_messages.append({"role": "assistant", "content": text or "",
                                 "tool_calls": tids})
            for j, (name, args) in enumerate(batch):
                with _AGENT_LOCK:
                    _AGENT["activity"] = "executing %s" % name
                sid = _agent_next_id()
                icon = _tool_icon(name)
                desc = _tool_desc(name, args)
                with _AGENT_LOCK:
                    _AGENT["steps"].append({"id": sid, "kind": "work", "text": desc,
                                            "state": "running", "icon": icon})
                # HARD GUARD: block ui_tap/ui_swipe unless the model has read
                # the screen (ui_dump in this batch, or a successful ui_dump /
                # auto-dump in a previous round) since the last screen change —
                # forces the model to read before tapping, not tap blind.
                if name in ("ui_tap", "ui_swipe") and not seen_screen:
                    result = ("BLOCKED: You must run ui_dump in the same round "
                              "before ui_tap/ui_swipe. Run ui_dump first to read "
                              "the screen, then decide your tap coordinates from "
                              "the screen state.")
                    ok = False
                else:
                    ok, result = _call_tool(name, args)
                if ok and name == "ui_dump":
                    # An explicit ui_dump's result is fed straight back to the
                    # model, so it now has real screen state to tap from.
                    seen_screen = True
                names.append(name)
                tcid = "chat_t%d_%d" % (rnd, j)
                print(f"🔧 /chat executed {name} ok={ok}")
                with _AGENT_LOCK:
                    _AGENT["tools_used"] += 1
                    if not ok:
                        _AGENT["last_error"] = "%s: %s" % (name, str(result)[:300])
                    for s in _AGENT["steps"]:
                        if s["id"] == sid:
                            s["state"] = "done" if ok else "error"
                            s["error"] = "" if ok else result
                llm_messages.append({"role": "tool", "tool_call_id": tcid,
                                     "name": name, "content": str(result)[:1200]})
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
    finally:
        with _AGENT_LOCK:
            _AGENT["running"] = False
            _AGENT["activity"] = "done"
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
    if names:
        wants_shot = bool(re.search(r'\b(screenshot|show me|show what|snapshot|capture)\b',
                                    user_message, re.IGNORECASE))
        if wants_shot and "ui_screenshot" not in names:
            try:
                _sok, _stxt = _call_tool("ui_screenshot", {})
                if _sok:
                    names.append("ui_screenshot")
            except Exception:
                pass
        acts = ", ".join(n for n in names if n in
                         ("ui_app_open", "ui_tap", "ui_swipe", "ui_type", "ui_key",
                          "ui_dump", "ui_screenshot", "ui_device"))
        sshot = "Captured screenshot (shown to you in a popup; not saved to disk)." if "ui_screenshot" in names else ""
        summary = ("I performed %d device actions (%s). %s" % (len(names), acts, sshot))
        if last_text and "FINAL" in last_text.upper():
            summary = last_text
        else:
            recap = _final_summary_call(active, llm_messages, names, last_screen)
            if recap:
                summary = recap
            else:
                summary += " The model didn't produce a final summary before the action cap."
        if last_screen and "ui_screenshot" not in names:
            snippet = last_screen.split("\n", 1)[1] if "\n" in last_screen else last_screen
            summary += "\nHere is what I last saw on screen:\n%s" % snippet[:600]
        with _AGENT_LOCK:
            _AGENT["last_reply"] = summary
        return summary
    with _AGENT_LOCK:
        _AGENT["last_reply"] = last_text or ""
    return last_text


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
            "Never defer back to the user with 'please provide commands' — you have the tools, so use them.\n"
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
            "HTTPS WARNING: if a ui_dump shows Chrome's 'Your connection is not private' / ERR_CERT / "
            "HSTS warning for the ITS portal, type thisisunsafe (ui_type {\"text\": \"thisisunsafe\"}) "
            "to bypass it and continue — the expired certificate is expected and safe. If ACEsi's "
            "server already auto-typed it, keep navigating from the fresh ui_dump.\n"
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
        reply = _chat_dispatch(llm_messages, user_message=user_message)
        if reply:
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
        # `flutter run` / `dart run` are long-lived dev sessions — stream to a
        # log file and return immediately instead of blocking forever.
        if re.match(r'^\s*(flutter\s+run|dart\s+run)\b', command, re.I):
            command = _resolve_run_device(command)
            if command is None:
                return False, 'flutter run needs a connected Android device (none found or locked/offline).'
            log_path = os.path.join(PROJECT_ROOT, 'run_%s.log' % uuid.uuid4().hex[:8])
            log = open(log_path, 'w', encoding='utf-8')
            proc = _popen(command, shell=True, stdout=log,
                                    stderr=subprocess.STDOUT, cwd=PROJECT_ROOT)
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

def _tool_icon(name):
    return {"list_files": "📂", "read_file": "📄", "grep": "🔍",
            "write_file": "✏️", "edit_file": "✏️",     "run_command": "▶"}.get(name, "🔧")
    return {"cdp_connect": "🔌", "cdp_evaluate": "💻", "cdp_console_logs": "📜",
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
            "restart": "🔄"}.get(name, "🔧")

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
    "list_files": "code", "read_file": "code", "grep": "code",
    "write_file": "code", "edit_file": "code", "run_command": "code",
    "git_status": "code", "git_log": "code", "git_commit": "code",
    "git_branch": "code", "git_merge": "code",
    "build_apk": "code", "pub_add": "code", "pub_remove": "code",
    "pub_upgrade": "code", "flutter_test": "code", "flutter_analyze": "code",
    # runtime controls
    "restart": "ctrl",
}


def _explicit_tool_domain(user_message):
    """If the user directly names a tool (e.g. 'use the curl tool', 'run ui_tap',
    'call ui_assert_text'), return that tool's domain (net/ui/code) so the
    dispatch loop skips the ambiguity gate and runs THAT tool directly. This is
    the 'ignore the menu — this is a direct instruction' case."""
    m = (user_message or "").lower()
    best = None
    for name, dom in _TOOL_DOMAINS.items():
        if name in m:
            # Prefer a concrete work domain (ui/net/code) over 'ctrl'.
            if dom != "ctrl":
                return dom
            best = best or dom
    return best


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
    code_strong = any(k in m for k in (
        "edit ", "replace ", "write file", "open file", "read file",
        "edit_file", "write_file", "read_file")) or \
        bool(re.search(_code_ext_re, m)) or \
        bool(re.search(r'\b(?:lib|src|test|assets)/[\w/]+\.\w+', m))
    domains = set()
    # A strong net request with no device ACTION is purely network work, even if
    # the URL hostname contains UI-ish words (e.g. ...univenierp...portal/...).
    if net_strong and not ui_action:
        return {"net"}
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
            "status code", "port ", "443", "8080", "dns", "no ports", "no web service")):
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


class _DomainGate(Exception):
    pass


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
   ui_screenshot {"name": "login", "save": true}  (captures the screen; by DEFAULT it is NOT saved to disk — it appears in a popup for Chris. Only pass save=true when Chris asked to keep it. You cannot view images)
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

def _terse_reply(text, max_len=500):
    """Condense a long prose narration into a short, plain recap. qwen2.5 on
    this box tends to narrate its whole reasoning chain instead of giving a
    short answer; we keep a compact final statement and drop the paragraph
    prose so Chris gets a text-message-style reply."""
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
    return last[:max_len].rstrip() + "…"

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
    _agent_reset()
    with _AGENT_LOCK:
        _AGENT["running"] = True
        _AGENT["activity"] = "planning"
    # Deterministic step-list executor (same as /chat): bypass the model for
    # explicit numbered UI scripts that qwen2.5:3b cannot follow.
    script_reply = _execute_ui_script(user_message)
    if script_reply:
        with _AGENT_LOCK:
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
                                            tool_choice="required" if force_tool else "auto")
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
            last_had_tools = bool(calls)
            final = _extract_final(reply)

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
                with _AGENT_LOCK:
                    _AGENT["activity"] = "done"
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

# Shared provider-fallback LLM call (Groq -> Cerebras -> OpenRouter -> Ollama).
# Returns (text, tool_calls) where tool_calls is a list of (name, args_dict).
# Passes the native tools= schema to the provider so the model can emit
# structured tool_calls instead of free-form prose (the stall fix).
def llm_reply(messages, max_tokens=2048, temperature=0.3, tool_choice="auto"):
    def one(name, endpoint, api_key, model):
        if not api_key:
            return None
        try:
            r = requests.post(f"{endpoint}/chat/completions",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": messages, "temperature": temperature,
                      "max_tokens": max_tokens, "tools": TOOLS_SCHEMA, "tool_choice": tool_choice},
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
                   "tools": TOOLS_SCHEMA, "tool_choice": tool_choice}
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


if __name__ == '__main__':
    # debug=False: Flask's dev reloader spawns a child that fights for port
    # 5000 with any old server still running, silently leaving the PHONE on
    # stale code (seen: qwen going off to Google because the deterministic
    # executor wasn't loaded). Reloads are handled by the ace_host watchdog
    # via its restart flag instead.
    app.run(host='0.0.0.0', port=5000, debug=False)