# -*- coding: utf-8 -*-
import sys
# Windows consoles/redirects default to cp1252; emoji prints crash with
# UnicodeEncodeError otherwise. Force UTF-8 with safe fallbacks.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import requests
import urllib3
urllib3.disable_warnings()
import json
import sqlite3
import os
import re
import winsound
import subprocess
import time
import tempfile
import threading
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

_status_lock = threading.Lock()
_status = {
    "status": "idle",
    "activity": "",
    "steps": [],
    "last_reply": "",
}

def _set_status(status=None, activity=None, steps=None, last_reply=None):
    with _status_lock:
        if status is not None:
            _status["status"] = status
        if activity is not None:
            _status["activity"] = activity
        if steps is not None:
            _status["steps"] = steps
        if last_reply is not None:
            _status["last_reply"] = last_reply

def _add_step(step_id, kind, text, icon="⚙️", state="running"):
    with _status_lock:
        steps = list(_status["steps"])
        existing = next((s for s in steps if s.get("id") == step_id), None)
        if existing:
            existing["state"] = state
            existing["text"] = text
        else:
            steps.append({"id": step_id, "kind": kind, "text": text, "icon": icon, "state": state})
        _status["steps"] = steps

def _clear_steps():
    with _status_lock:
        _status["steps"] = []

# ──────────────────────────────────────────────────────────────────────────────
# Lightweight web search using DuckDuckGo HTML endpoint (no API key required).
# Returns a short summary string built from the top result titles + snippets.
# ──────────────────────────────────────────────────────────────────────────────
def web_search(query, max_results=3):
    try:
        url = 'https://html.duckduckgo.com/html/'
        resp = requests.post(url, data={'q': query}, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if resp.status_code != 200:
            return f"Search failed (HTTP {resp.status_code})."
        text = resp.text
        titles = re.findall(r'<h2 class="result__title">.*?<a[^>]*>(.*?)</a>', text, re.S)
        snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', text, re.S)
        if not titles and not snippets:
            return "No search results found."
        clean = lambda s: re.sub(r'<[^>]+>', '', s).strip()
        lines = []
        for i in range(min(max_results, max(len(titles), len(snippets)))):
            t = clean(titles[i]) if i < len(titles) else ''
            s = clean(snippets[i]) if i < len(snippets) else ''
            if t:
                lines.append(f"- {t}")
            if s:
                lines.append(f"  {s}")
        return "\n".join(lines)
    except Exception as e:
        return f"Search error: {e}"


def _sanitize_response(reply):
    """Strip any romantic/sexual/pet-name language from model output."""
    if not reply:
        return reply
    lower = reply.lower()
    forbidden_terms = [
        'partner', 'presence', 'warmth', 'gentle', 'slow', 'hold space',
        'intimate', 'romantic', 'love', 'darling', 'honey', 'babe',
        'sweetheart', 'pet names', 'stay warm', 'match his', 'linger',
        'soften', 'hardcore', 'raw', 'connect', 'deep bond'
    ]
    hits = [t for t in forbidden_terms if t in lower]
    if hits:
        return "(Response blocked: contains inappropriate language. Redirecting to work mode.)"
    return reply


def _looks_like_dont_know(reply):
    if not reply:
        return True
    lowered = reply.lower()
    cues = [
        "i don't actually know",
        "i don't know",
        "i'm not sure",
        "i wouldn't want to guess",
        "i don't have access",
        "i can't give you the definitive answer",
        "i'm unable to",
        "i don't have the ability",
        "i cannot answer that",
        "no access to",
    ]
    return any(cue in lowered for cue in cues)


def take_screenshot(path=None):
    from PIL import ImageGrab
    if path is None:
        path = os.path.join(tempfile.gettempdir(), f'ace_ui_{int(time.time())}.png')
    img = ImageGrab.grab()
    img.save(path)
    return path


def search_local_files(folder, query):
    matches = []
    query_lower = query.lower()
    for root, dirs, files in os.walk(folder):
        for f in files:
            if query_lower in f.lower():
                matches.append(os.path.join(root, f))
    return matches[:20]


def _handle_pc_run_command(cmd):
    suspicious, pattern = _check_command_security(cmd)
    if suspicious:
        _security_alert("suspicious_command", f"Pattern: {pattern}, Command: {cmd[:200]}")
        return f"Command blocked: matches suspicious pattern '{pattern}'. If this is intentional, contact Chris."
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.abspath(os.path.dirname(__file__))
        )
        if result.returncode != 0:
            with _security_lock:
                _security_state["failed_commands"] += 1
                if _security_state["failed_commands"] >= 5:
                    _security_alert("multiple_failures", f"{_security_state['failed_commands']} failed commands in a row")
                    _security_state["failed_commands"] = 0
        else:
            with _security_lock:
                _security_state["failed_commands"] = 0
        out = result.stdout[-4000:] if result.stdout else ""
        err = result.stderr[-2000:] if result.stderr else ""
        if out and err:
            return f"Command finished with code {result.returncode}.\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        elif out:
            return f"Command finished with code {result.returncode}.\n{out}"
        elif err:
            return f"Command finished with code {result.returncode}.\n{err}"
        return f"Command finished with code {result.returncode}. No output."
    except subprocess.TimeoutExpired:
        _security_alert("command_timeout", f"Command timed out after 300s: {cmd[:200]}")
        return "Command timed out after 300 seconds."
    except Exception as e:
        _security_alert("command_error", f"{type(e).__name__}: {str(e)}")
        return f"Command failed: {e}"


def _handle_edit_file(path, old_text, new_text):
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        return f"File not found: {abs_path}"
    sensitive, pattern = _check_file_access_security(abs_path)
    if sensitive:
        _security_alert("sensitive_file_access", f"Pattern: {pattern}, Path: {abs_path}")
        return f"Access blocked: file matches sensitive pattern '{pattern}'. If this is intentional, contact Chris."
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            current = f.read()
        if old_text not in current:
            with _security_lock:
                _security_state["failed_edits"] += 1
                if _security_state["failed_edits"] >= 5:
                    _security_alert("multiple_edit_failures", f"{_security_state['failed_edits']} failed edits in a row")
                    _security_state["failed_edits"] = 0
            return f"Edit failed: the old text was not found in {abs_path}"
        updated = current.replace(old_text, new_text, 1)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(updated)
        with _security_lock:
            _security_state["failed_edits"] = 0
        return f"Edited {abs_path}: replaced the old text with the new text."
    except Exception as e:
        _security_alert("edit_error", f"{type(e).__name__}: {str(e)}")
        return f"Edit failed: {e}"


def ui_dump_and_search(folder, query, wants_text=False):
    shot = take_screenshot()
    _add_step("ui_dump", "work", "Screenshot captured", "📸", "done")
    _add_step("ui_dump", "work", "Reading screen…", "👁️", "running")
    screen_hit = False
    screen_text = ''
    try:
        text = ocr_image(shot)
        screen_text = text
        screen_hit = query.lower() in text.lower()
    except Exception:
        pass
    name_matches = []
    if query:
        name_matches = search_local_files(folder, query)
    desc = _describe_screen(screen_text, query, screen_hit, name_matches, folder, wants_text)
    _add_step("ui_dump", "work", "Done", "✅", "done")
    return desc


def _clean_ocr_text(text):
    """Clean up noisy OCR output into readable lines."""
    if not text:
        return ''
    # Replace common OCR garble
    text = text.replace('�', "'")
    text = text.replace('|', 'I')
    text = text.replace('\u0007', ' ')
    # Normalize whitespace and split into lines
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip lines that have no letters at all
        if not any(c.isalpha() for c in line):
            continue
        # Skip lines that are almost entirely non-letters
        if len(line) > 3 and sum(1 for c in line if c.isalpha()) / len(line) < 0.15:
            continue
        # Collapse repeated words: "ACEsi ACEsi" -> "ACEsi"
        words = line.split()
        deduped = []
        prev = None
        for w in words:
            if w != prev:
                deduped.append(w)
            prev = w
        line = ' '.join(deduped)
        cleaned.append(line)
    # Deduplicate adjacent identical lines
    final = []
    prev = None
    for line in cleaned:
        if line != prev:
            final.append(line)
        prev = line
    return '\n'.join(final)


def _describe_screen(ocr_text, query, screen_hit, name_matches, folder, wants_text=False):
    cleaned = _clean_ocr_text(ocr_text)
    lines = []
    if wants_text:
        if cleaned:
            summary = _summarize_screen_text(cleaned)
            lines.append(summary)
        else:
            lines.append("I couldn't read any text from the screen.")
    elif cleaned:
        lines.append("Here's what I see on your screen right now:")
        lines.append(cleaned[:300])
    else:
        lines.append("I couldn't read any text from the screen.")
    if query:
        lines.append(f"I searched for '{query}' on the screen: {'found it' if screen_hit else 'not visible right now'}.")
        if name_matches:
            lines.append(f"I also found {len(name_matches)} file(s) matching '{query}' in your Pictures folder:")
            for m in name_matches[:5]:
                lines.append(f"  {m}")
        else:
            if query:
                lines.append(f"No files matching '{query}' by name in {folder}.")
    return "\n".join(lines)


def _summarize_screen_text(ocr_text):
    prompt = (
        "You are ACE. The user asked you to tell them what text is on their screen. "
        "Read the following OCR text from their screen and describe what you see in 2-4 short sentences. "
        "Focus on what is being shown (e.g., code editor, file names, application names, readable content). "
        "Do not mention OCR errors or noise. If it's mostly an IDE or editor, say so and mention the file or project name if visible.\n\n"
        f"Screen text:\n{ocr_text[:2000]}"
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    for model_id in [OPENROUTER_MODEL] + [m for m in FALLBACK_MODELS if m != OPENROUTER_MODEL]:
        try:
            resp = requests.post(
                f"{OPENROUTER_ENDPOINT}/chat/completions",
                headers=headers,
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "Tell me what text is on my screen."}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 300
                },
                timeout=(10, 120)
            )
            if resp.status_code == 200:
                msg = resp.json()["choices"][0]["message"]
                reply = msg.get("content") or msg.get("reasoning")
                if reply:
                    reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S).strip()
                if reply:
                    return reply
        except Exception:
            continue
    # Fallback: show raw text
    return f"Here's the text on your screen:\n{ocr_text[:800]}"


def _do_research_and_answer(user_message, original_reply):
    _add_step("research", "work", "Searching the web…", "🔎", "running")
    _set_status(activity="Researching…")
    search_query = user_message
    search_result = web_search(search_query)
    _add_step("research", "work", "Summarizing findings", "📚", "running")
    research_prompt = (
        "You are ACE. The user asked a question and your first answer was uncertain. "
        "Use the following web search results to give a confident, specific answer. "
        "If the results still don't contain a clear answer, say so honestly and give the best "
        "context you can.\n\n"
        f"User question: {user_message}\n\n"
        f"Search results:\n{search_result}\n\n"
        "Now answer the user's question directly."
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }
    max_retries = 2
    for model_id in [OPENROUTER_MODEL] + [m for m in FALLBACK_MODELS if m != OPENROUTER_MODEL]:
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    f"{OPENROUTER_ENDPOINT}/chat/completions",
                    headers=headers,
                    json={
                        "model": model_id,
                        "messages": [
                            {"role": "system", "content": research_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 700
                    },
                    timeout=(10, 120)
                )
                if resp.status_code == 200:
                    msg = resp.json()["choices"][0]["message"]
                    reply = msg.get("content") or msg.get("reasoning")
                    if reply:
                        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S).strip()
                    if not reply:
                        reply = original_reply
                    _add_step("research", "work", "Research complete", "✅", "done")
                    return reply
                print(f"⚠️ Research model {model_id} returned {resp.status_code}")
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    continue
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    continue
        _add_step("research", "work", f"{model_id} failed, trying fallback…", "⚠️", "error")
    _add_step("research", "work", "Research failed", "❌", "error")
    return original_reply

OPENROUTER_API_KEY = "REDACTED_OPENROUTER_KEY"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "google/gemma-4-31b-it:free"
# Free-tier pools get crowded; fall through these when the primary 429s/fails.
FALLBACK_MODELS = [
    "z-ai/glm-5.2:free",
    "poolside/laguna-s-2.1:free",
    "thinkingmachines/inkling-small:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
]

NTF_TOPIC = "ace_alerts"
NTFY_SERVER = "https://ntfy.sh"

_security_lock = threading.Lock()
_security_state = {
    "failed_commands": 0,
    "failed_edits": 0,
    "sensitive_access": 0,
    "last_alert_time": 0,
    "alert_cooldown": 300,
}


def _send_ntfy(title, message, priority="high"):
    try:
        requests.post(
            f"{NTFY_SERVER}/{NTF_TOPIC}",
            data=message,
            headers={"Priority": priority, "Title": title},
            timeout=10
        )
    except Exception:
        pass


def _security_alert(threat_type, details):
    with _security_lock:
        now = time.time()
        if now - _security_state["last_alert_time"] < _security_state["alert_cooldown"]:
            return
        _security_state["last_alert_time"] = now
    title = f"ACEsi Security Alert: {threat_type}"
    message = f"Threat: {threat_type}\nDetails: {details}\nTime: {datetime.now().isoformat()}"
    threading.Thread(target=_send_ntfy, args=(title, message), daemon=True).start()


def _check_command_security(cmd):
    suspicious_patterns = [
        r'rm\s+-rf\s+/',
        r'del\s+/[sS]',
        r'format\s+[cC]:',
        r'shutdown',
        r'reboot',
        r'curl.*\|\s*sh',
        r'wget.*\|\s*sh',
        r'powershell.*-enc',
        r'powershell.*-encoded',
        r'net\s+user',
        r'net\s+localgroup',
        r'reg\s+delete',
        r'reg\s+add',
        r'schtasks',
        r'at\s+\d+',
        r'\.env',
        r'api[_-]?key',
        r'secret',
        r'password',
        r'token',
        r'credentials',
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, pattern
    return False, None


def _check_file_access_security(path):
    sensitive_patterns = [
        r'\.env$',
        r'\.key$',
        r'\.pem$',
        r'\.p12$',
        r'\.pfx$',
        r'credentials',
        r'secrets',
        r'\.ssh/',
        r'\.aws/',
        r'\.git/config',
    ]
    for pattern in sensitive_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            return True, pattern
    return False, None

EMBER_DEFINITION = "Ember is a project codename. When either of us says it, we switch to focused, heads-down work mode — present, direct, and completely locked in on the task. No small talk, just execution."

def init_db():
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, role TEXT, content TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS memory (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated TEXT
    )''')
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

LAST_FILE_PATH = None

@app.route('/')
def index():
    return send_from_directory('.', 'ACEsi.html')

@app.route('/chat', methods=['POST'])
def chat():
    _clear_steps()
    _set_status(status="busy", activity="Thinking…")
    _add_step("receive", "work", "Received message", "📨", "done")

    data = request.json
    user_message = data.get('message', '')
    save_conversation("user", user_message)

    # Handle file read requests
    global LAST_FILE_PATH
    file_read_match = re.search(r'(?:read|open)\s+(?:file\s+)?(.+?)(?:\s+(?:file|please))?$', user_message, re.IGNORECASE)
    if file_read_match:
        is_open = re.match(r'open\b', user_message, re.IGNORECASE) is not None
        candidate = file_read_match.group(1).strip().strip('"\'')
        candidate = re.sub(r'^(?:the|this|that)?\s*file\s*:\s*', '', candidate, flags=re.IGNORECASE).strip()
        candidate = re.sub(r'\b(?:in|on)\s+(?:my\s+)?(?:documents|document)\b', '', candidate, flags=re.IGNORECASE)
        candidate = re.sub(r'\bon\s+my\s+computer\b', '', candidate, flags=re.IGNORECASE).strip()
        vague = candidate.lower() in ('the', 'it', 'this', 'that', 'file', 'the file', 'this file', 'that file', 'previous', 'last')
        if vague and LAST_FILE_PATH:
            file_path = LAST_FILE_PATH
        elif not vague:
            file_path = candidate
        else:
            file_path = None
    else:
        file_path = None
    if file_path:
        COMMON_EXTS = ('.pdf', '.txt', '.png', '.jpg', '.jpeg', '.docx', '.md')
        if not os.path.isabs(file_path):
            doc_base = os.path.join(os.path.expanduser('~'), 'Documents')
            proj_base = 'C:\\Users\\chris\\StudentSyncSA'
            doc_path = os.path.join(doc_base, file_path)
            proj_path = os.path.join(proj_base, file_path)
            if os.path.exists(doc_path):
                file_path = doc_path
            elif os.path.exists(proj_path):
                file_path = proj_path
            else:
                for ext in COMMON_EXTS:
                    if os.path.exists(doc_path + ext):
                        file_path = doc_path + ext
                        break
                    if os.path.exists(proj_path + ext):
                        file_path = proj_path + ext
                        break
        else:
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
                    content = ocr_pdf(file_path)
            elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'):
                content = ocr_image(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            LAST_FILE_PATH = file_path
            if is_open:
                os.startfile(file_path)
                print(f"🖥️ Opened file in default viewer: {file_path}")
            user_message = f"[File content of {file_path}]:\n{content}\n\n---\nUser asked: {user_message}"
            print(f"📖 Read file: {file_path} ({len(content)} chars)")
            _add_step("read_file", "work", f"Read {file_path}", "📖", "done")
        except Exception as e:
            _set_status(status="error", activity="Failed to read file")
            _add_step("read_file", "work", f"Read {file_path}", "📖", "error")
            return jsonify({"reply": f"❌ Could not read file: {e}"})

    # Greeting check
    if user_message.lower().strip() in ["hello", "hi"]:
        reply = "Morning, Chris. What are we working on today?"
        reply = _sanitize_response(reply)
        save_conversation("assistant", reply)
        _set_status(status="idle", activity="", last_reply=reply)
        return jsonify({"reply": reply})

    model = OPENROUTER_MODEL

    if "ember" in user_message.lower():
        reply = EMBER_DEFINITION
        reply = _sanitize_response(reply)
        save_conversation("assistant", reply)
        _set_status(status="idle", activity="", last_reply=reply)
        return jsonify({"reply": reply})

    if "auto-fix" in user_message.lower():
        file_match = re.search(r'(lib/[\w/]+\.dart)', user_message)
        error_match = re.search(r'error is:\s*(.+?)(\.|$)', user_message, re.IGNORECASE)
        if file_match and error_match:
            file_path = file_match.group(1)
            error_text = error_match.group(1)
            _add_step("auto_fix", "work", f"Auto-fix {file_path}", "🔧", "done")
            return jsonify({
                "type": "stream",
                "url": f"/auto_fix_stream?file_path={file_path}&error_text={error_text}"
            })
        else:
            _set_status(status="idle", activity="")
            return jsonify({"reply": "I need a file path and error description. Say: 'auto-fix lib/path/file.dart. The error is: ...'"})

    # ── Device commands: executed against the phone via the CDP bridge ──
    # Supports batches: each line of the message is parsed as its own command.
    device_reply = _device_command_reply(user_message)
    if device_reply is not None:
        save_conversation("assistant", device_reply)
        _set_status(status="idle", activity="", last_reply=device_reply)
        return jsonify({"reply": device_reply})

    try:
        _set_status(activity="Reading message…")
        print(f"📨 Incoming message length: {len(user_message)} chars")
        max_chars = 8000
        if len(user_message) > max_chars:
            user_message = user_message[:max_chars] + "\n\n[Message truncated...]"
            print(f"✂️ Truncated to {max_chars} chars")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        }
        print(f"🔗 Calling OpenRouter: {OPENROUTER_ENDPOINT}/chat/completions with model={model}")
        _set_status(activity="Calling model…")
        _add_step("call_model", "work", f"Calling {model}", "🔗", "running")

        max_retries = 2
        response = None
        for model_id in [model] + [m for m in FALLBACK_MODELS if m != model]:
            for attempt in range(max_retries + 1):
                try:
                    response = requests.post(
                        f"{OPENROUTER_ENDPOINT}/chat/completions",
                        headers=headers,
                        json={
                            "model": model_id,
                            "messages": [
                                {"role": "system", "content": "You are ACE, a technical work assistant for Chris. STRICT RULES: 1) Never use romantic language, sexual content, pet names, emotional intimacy, or roleplay as a partner. 2) Never mention 'partner', 'presence', 'warmth', 'gentle', 'slow', 'hold space', or similar terms. 3) Never reference 'Ember' as anything other than a project codename for focused work mode. 4) Respond only as a technical assistant. Be direct, concise, technical. 5) If unsure, say so. Never invent code or paths. 6) Keep responses short unless detail is needed. 7) Use exact file paths and line numbers when relevant. 8) Match existing code style. Do not refactor unless asked. 9) No small talk, no personal questions, no emotional language. 10) If asked about personal/romantic topics, decline and redirect to work."},
                                {"role": "user", "content": user_message}
                            ],
                            "temperature": 0.5,
                            "max_tokens": 700
                        },
                        timeout=(10, 120)
                    )
                    break
                except requests.exceptions.Timeout:
                    if attempt < max_retries:
                        print(f"⏱️ Timeout, retry {attempt + 1}/{max_retries}...")
                        _set_status(activity=f"Timeout, retry {attempt + 1}…")
                        continue
                    raise
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries:
                        print(f"🔌 Connection error, retry {attempt + 1}/{max_retries}...")
                        _set_status(activity=f"Connection error, retry {attempt + 1}…")
                        continue
                    raise
            if response is not None and response.status_code == 200:
                break
            print(f"⚠️ Model {model_id} returned {response.status_code if response else 'no response'}; trying next fallback")
            _add_step("call_model", "work", f"{model_id} failed, trying fallback…", "⚠️", "error")

        print(f"📥 OpenRouter response: status={response.status_code}")
        if response.status_code == 200:
            msg = response.json()["choices"][0]["message"]
            reply = msg.get("content") or msg.get("reasoning")
            if reply:
                reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.S).strip()
            if not reply:
                reply = "(ACE got an empty response from the model — please try again.)"
            print(f"✅ Reply length: {len(reply)} chars")
            if _looks_like_dont_know(reply):
                print("🔎 Reply looks uncertain — triggering research…")
                _add_step("call_model", "work", "Answer uncertain, researching…", "🔎", "running")
                reply = _do_research_and_answer(user_message, reply)
            reply = _sanitize_response(reply)
            save_conversation("assistant", reply)
            _add_step("call_model", "work", f"Reply from {model}", "✅", "done")
            _set_status(status="idle", activity="", last_reply=reply)
            return jsonify({"reply": reply})
        else:
            print(f"❌ OpenRouter error: {response.text}")
            _add_step("call_model", "work", f"Model error {response.status_code}", "❌", "error")
            _set_status(status="error", activity="Model error")
            return jsonify({"reply": f"Error: {response.status_code}"})
    except Exception as e:
        print(f"💥 Exception in /chat: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        _add_step("call_model", "work", f"Exception: {type(e).__name__}", "💥", "error")
        _set_status(status="error", activity=str(e))
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
    data = request.json
    command = data.get('command', '')
    try:
        if "scrcpy" in command.lower():
            subprocess.Popen('start cmd /k "scrcpy"', shell=True)
            return jsonify({'output': '✅ Scrcpy launched'})
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = os.listdir('C:\\Users\\chris\\StudentSyncSA')
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)})

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

@app.route('/auto_fix_stream', methods=['GET'])
def auto_fix_stream():
    file_path = request.args.get('file_path')
    error_text = request.args.get('error_text')

    if not file_path or not error_text:
        return "Missing parameters", 400

    def generate():
        yield "Reading file...\n\n"
        time.sleep(0.5)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            yield "File read successfully.\n\n"
            time.sleep(0.5)
        except Exception as e:
            yield f"Failed to read file: {str(e)}\n\n"
            return

        yield "Generating fix...\n\n"
        time.sleep(0.5)
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENROUTER_API_KEY}"
            }
            fix_response = requests.post(
                f"{OPENROUTER_ENDPOINT}/chat/completions",
                headers=headers,
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": f"You are ACE, an expert debugger. Fix the following code. The error is: {error_text}. Respond with only the fixed code — no explanations."},
                        {"role": "user", "content": content}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 400
                },
                timeout=(10, 120)
            )
            if fix_response.status_code == 200:
                fixed_code = fix_response.json()["choices"][0]["message"]["content"]
                yield "Fix generated.\n\n"
                time.sleep(0.5)
            else:
                yield f"Fix generation failed: {fix_response.status_code}\n\n"
                return
        except Exception as e:
            yield f"Fix generation error: {str(e)}\n\n"
            return

        yield "Applying fix...\n\n"
        time.sleep(0.5)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            yield "Fix applied successfully!\n\n"
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
                data=f"ACE fixed it! Auto-fix applied to {file_path}.",
                headers={"Priority": "high", "Title": "ACE fixed it!"},
                timeout=10
            )
            yield "Notification sent.\n\n"
        except Exception as e:
            yield f"ntfy error: {e}\n\n"

        yield "Auto-fix complete.\n\n"

    response = Response(generate(), mimetype='text/plain')
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# ──────────────────────────────────────────────────────────────
# CDP (Chrome DevTools Protocol) — JavaScript injection for WebView
# ──────────────────────────────────────────────────────────────

# Store active CDP connection per device
_cdp_sessions = {}

def _cdp_connect(device_id=None, target_url=None):
    """Connect to Chrome DevTools Protocol on an Android WebView.

    Discovers the actual devtools socket (webview_devtools_remote_<pid> or
    chrome_devtools_remote), forwards it to tcp:9222 and attaches to a page
    target (matching target_url if given) so Runtime.evaluate hits the page.
    """
    serial = f"-s {device_id}" if device_id else ""
    try:
        # 1. Find the devtools socket(s) exposed by the device.
        out = subprocess.run(
            f"adb {serial} shell cat /proc/net/unix",
            shell=True, capture_output=True, text=True, timeout=10
        ).stdout
        sockets = []
        for line in out.splitlines():
            parts = line.split()
            if parts and "devtools_remote" in parts[-1]:
                sockets.append(parts[-1].lstrip("@"))
        if not sockets:
            print("CDP connect error: no devtools sockets found on device")
            return None
        webviews = [s for s in sockets if s.startswith("webview_devtools_remote")]
        chrome = [s for s in sockets if s == "chrome_devtools_remote"]
        sock = (webviews or chrome or sockets)[0]

        # 2. Forward a local port to that exact socket.
        subprocess.run(f"adb {serial} forward --remove tcp:9222",
                       shell=True, capture_output=True, timeout=10)
        subprocess.run(f"adb {serial} forward tcp:9222 localabstract:{sock}",
                       shell=True, capture_output=True, timeout=10)

        # 3. Connect to the browser-level WebSocket (reliable for WebView,
        #    unlike the HTTP /json page list which is often empty).
        import urllib.request
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        version = json.loads(opener.open(
            "http://127.0.0.1:9222/json/version", timeout=5).read().decode("utf-8"))
        ws_url = version.get("webSocketDebuggerUrl")
        if not ws_url:
            print("CDP connect error: no webSocketDebuggerUrl")
            return None

        import websocket
        # suppress_origin: Chrome/WebView >=111 rejects the WebSocket
        # handshake with 403 if an Origin header is present.
        # timeout: bound recv() so a silent peer can't hang the request.
        return websocket.create_connection(ws_url, suppress_origin=True,
                                           timeout=10,
                                           enable_multithread=True)
    except Exception as e:
        print(f"CDP connect error: {e}")
    return None

# CDP message ids must stay small: the Android WebView devtools server
# silently ignores commands whose id exceeds 32-bit integer range.
_cdp_id_counter = 0

def _cdp_send(ws, method, params=None, session_id=None):
    """Send a CDP command and return the response."""
    if not ws:
        return {"error": "No CDP connection"}
    global _cdp_id_counter
    _cdp_id_counter = (_cdp_id_counter % 100000) + 1
    msg_id = _cdp_id_counter
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    if session_id:
        msg["sessionId"] = session_id
    ws.send(json.dumps(msg))
    # Wait for response (bounded by the websocket timeout)
    while True:
        try:
            response = json.loads(ws.recv())
            if response.get("id") == msg_id:
                return response
        except Exception as e:
            return {"error": f"CDP recv failed: {e}"}
    return {"error": "No response"}

def _cdp_js_inject(ws, js_code, session_id=None):
    """Inject JavaScript via CDP Runtime.evaluate."""
    return _cdp_send(ws, "Runtime.evaluate", {
        "expression": js_code,
        "awaitPromise": True,
        "returnByValue": True,
        "userGesture": True
    }, session_id=session_id)


def _build_fill_js(field, value):
    """Build JS that sets a form field (select/input/textarea) by name/id."""
    f = json.dumps(field)
    v = json.dumps(value)
    fd = json.dumps(field + "_desc")
    return (
        "(function(){"
        "var els=document.getElementsByName(" + f + ");"
        "var el=els.length?els[0]:document.getElementById(" + f + ");"
        "if(!el){return 'FIELD NOT FOUND: '+" + f + "}"
        "var out;"
        "if(el.tagName==='SELECT'){"
        "var vv=" + v + ";var found=false;"
        "for(var i=0;i<el.options.length;i++){"
        "var ov=String(el.options[i].value);var ot=el.options[i].text.trim();"
        "if(ov===vv||ot.toUpperCase()===vv.toUpperCase()){el.value=ov;found=true;break}}"
        "if(!found){return 'OPTION NOT FOUND: '+vv+' | options: '+"
        "Array.from(el.options).map(function(o){return o.value+'='+o.text.trim()}).join(', ')}"
        "out=el.options[el.selectedIndex].text.trim();"
        "var d=document.getElementById(" + fd + ")||document.getElementsByName(" + fd + ")[0];"
        "if(d&&el.selectedIndex>=0){d.value=out}"
        "}else{el.value=" + v + ";out=el.value}"
        "el.dispatchEvent(new Event('input',{bubbles:true}));"
        "el.dispatchEvent(new Event('change',{bubbles:true}));"
        "return 'SET '+" + f + "+'='+out"
        "})()"
    )


FORM_DUMP_JS = (
    "(function(){var els=document.querySelectorAll('input,select,textarea');"
    "var o=[];"
    "for(var i=0;i<els.length&&o.length<40;i++){var e=els[i];"
    "if(e.type==='hidden')continue;"
    "var val=(e.tagName==='SELECT'&&e.selectedIndex>=0)?e.options[e.selectedIndex].text.trim():String(e.value||'').slice(0,25);"
    "o.push((e.name||e.id||'?')+'['+(e.type||e.tagName.toLowerCase())+']='+val)}"
    "return o.length?('FIELDS: '+o.join(' | ')):'NO FIELDS ON PAGE'})()"
)


def _build_click_js(text):
    """Build JS that clicks the first button/link whose label contains text."""
    t = json.dumps(text)
    return (
        "(function(){var tt=" + t + ".toUpperCase();"
        "var cands=document.querySelectorAll('button,input[type=submit],input[type=button],a,[role=button]');"
        "for(var i=0;i<cands.length;i++){var c=cands[i];"
        "var label=String(c.value||c.textContent||'').trim();"
        "if(!label)continue;"
        "if(label.toUpperCase().indexOf(tt)>=0){c.click();return 'CLICKED: '+label.slice(0,40)}}"
        "return 'BUTTON NOT FOUND: '+tt})()"
    )


AUTOFILL_DART_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "lib", "services", "autofill_script.dart")
PROFILE_HIVE_REMOTE = ("/data/data/com.studentsyncsa.studentsyncsa/"
                       "app_flutter/student_profile.hive")


def _pull_profile_json():
    """Pull the live StudentProfile JSON out of the phone's Hive box via adb.
    Hive stores as UTF-16 LE; extract the LAST complete JSON (most recent save)."""
    try:
        p = subprocess.run(
            ["adb", "shell", "run-as", "com.studentsyncsa.studentsyncsa",
             "cat", PROFILE_HIVE_REMOTE],
            capture_output=True, timeout=20)
    except Exception as e:
        return None, f"adb failed: {e}"
    if p.returncode != 0 or not p.stdout:
        return None, ("could not read profile box "
                      + p.stderr.decode("utf-8", "replace")[:200])
    raw = p.stdout
    # Hive box: header + frames; the JSON value is plain UTF-8. Multiple
    # saves leave older frames behind — take the LAST valid {"id" object.
    txt = raw.decode("utf-8", errors="ignore")
    import re
    starts = [m.start() for m in re.finditer(r'\{"id"', txt)]
    for start in reversed(starts):
        depth = 0
        in_str = False
        esc = False
        end = None
        for i in range(start, len(txt)):
            c = txt[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end:
            blob = txt[start:end]
            try:
                json.loads(blob)  # validate
                return blob, None
            except json.JSONDecodeError:
                continue
    return None, "no valid JSON profile found in Hive box"


def _dart_unescape(s):
    """Apply Dart string-literal escape rules (the _script template is a
    non-raw ''' string, so \\n, \\d etc. are single-char/\\ at runtime)."""
    out = []
    i = 0
    simple = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f",
              "v": "\v", "'": "'", '"': '"', "\\": "\\", "`": "`", "$": "$"}
    while i < len(s):
        c = s[i]
        if c != "\\" or i + 1 >= len(s):
            out.append(c)
            i += 1
            continue
        nxt = s[i + 1]
        if nxt == "u" and i + 2 < len(s) and s[i + 2] == "{":
            end = s.find("}", i + 3)
            if end > 0:
                try:
                    out.append(chr(int(s[i + 3:end], 16)))
                    i = end + 1
                    continue
                except ValueError:
                    pass
        if nxt in simple:
            out.append(simple[nxt])
            i += 2
            continue
        # Unknown escape: Dart keeps the char as-is.
        out.append(nxt)
        i += 2
    return "".join(out)


def _build_profile_autofill_js(profile_json, extra_map=None):
    """Assemble the app's own autofill engine (autofill_script.dart) with a
    real profile injected. addFloatingStar=false => auto-runs doAutofill().
    extra_map: additional UNIVEN-specific field->value pairs derived straight
    from the profile (the Dart itsExact map lacks oapSurname etc.)."""
    dart = open(AUTOFILL_DART_PATH, encoding="utf-8").read()
    m_dp = re.search(r"const String ssaDatePickerJs = r?'''(.*?)''';",
                     dart, re.DOTALL)
    dp = m_dp.group(1) if m_dp else ""  # raw string: no unescaping
    m_tpl = re.search(
        r"String _script\(String profileJson[^)]*\)\s*\{\s*return '''(.*?)''';\s*\}",
        dart, re.DOTALL)
    if not m_tpl:
        raise RuntimeError("autofill template not found in autofill_script.dart")
    tpl = _dart_unescape(m_tpl.group(1))
    tpl = re.sub(r"\$\{addFloatingStar \? '''.*?\}''' : ''\}", "", tpl,
                 flags=re.DOTALL)
    tpl = tpl.replace("${!addFloatingStar ? 'doAutofill();' : ''}",
                      "__ssaFillAll();\n  doAutofill();")
    # ── Patch: the Dart source declares `filled` and toasts about it but
    # NEVER defines the actual field-filling loop. Supply it here.
    tpl = tpl.replace(
        "function doAutofill() {",
        "function doAutofill() {\n    var filled = 0;", 1)
    fill_all = (
        "function __ssaFillAll(){\n"
        "  var n=0,f=document.querySelectorAll('input,select,textarea');\n"
        "  if(!window.__ssaExactUp){window.__ssaExactUp={};\n"
        "   for(var kk in itsExact){window.__ssaExactUp[kk.toUpperCase()]=itsExact[kk];}}\n"
        "  var EXTRA=" + json.dumps({(k or '').upper(): v
                                     for k, v in (extra_map or {}).items()
                                     if v}) + ";\n"
        "  for(var i=0;i<f.length;i++){var el=f[i];\n"
        "   if(!el.name&&!el.id)continue;\n"
        "   var t=(el.type||'').toLowerCase();\n"
        "   if(t==='submit'||t==='button'||t==='file'||t==='image'||t==='reset')continue;\n"
        "   if(t==='checkbox'||t==='radio'&&false)continue;\n"
        "   var k=String(el.name||el.id||'').toUpperCase().trim();\n"
        "   var v=EXTRA[k];\n"
        "   if(v===undefined||v===null||v==='')v=window.__ssaExactUp[k];\n"
        "   if(v===undefined||v===null||v==='')continue;\n"
        "   try{if(fill(el,v))n++;}catch(e){}\n"
        "  }\n"
        "  return n;\n"
        "}\n")
    anchor = "window.requestFlutterAutofill = doAutofill;"
    if anchor not in tpl:
        raise RuntimeError("autofill anchor not found")
    tpl = tpl.replace(anchor, fill_all + anchor, 1)
    tpl = tpl.replace("$ssaDatePickerJs", dp)
    tpl = tpl.replace("$profileJson", profile_json)
    leftover = re.findall(r"\$\{[A-Za-z_][^}]*\}", tpl)
    if leftover:
        raise RuntimeError("unresolved Dart interpolations: %s" % leftover[:3])
    return tpl


_UI_CSS = """
/* StudentSyncSA My Profile replica (AppColors / AppTheme.dark) */
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%!important}
body{background:linear-gradient(180deg,#0D2158 0%,#0F1624 45%,#181818 100%)
 !important;background-attachment:fixed!important;color:#F8FAFC!important;
 overflow-x:hidden!important;font-family:Roboto,system-ui,sans-serif!important;
 padding-top:118px!important;padding-bottom:96px!important}
table,form,div,td,th,tr,input,select,textarea,button,p,h1,h2,h3,h4,span,label{
 max-width:100%!important;box-sizing:border-box!important}
form{padding:0 20px!important}
table{display:block!important;width:100%!important;overflow-x:visible!important;
 background:transparent!important;border:none!important}
tbody{display:block!important;width:100%!important}
/* ── app bar ── */
#ssa-appbar{position:fixed;top:0;left:0;right:0;z-index:2147483000;height:56px;
 display:flex;align-items:center;justify-content:center;
 background:rgba(15,22,36,.92);backdrop-filter:blur(8px)}
#ssa-appbar span{color:#F8FAFC;font-size:18px;font-weight:600}
/* ── progress bar + step text ── */
#ssa-prog{position:fixed;top:56px;left:0;right:0;z-index:2147483000;
 background:rgba(15,22,36,.92);backdrop-filter:blur(8px);
 padding:16px 24px 6px 24px}
#ssa-prog .bar{display:flex;margin-bottom:8px}
#ssa-prog .seg{height:4px;border-radius:2px;flex:1;margin:0 2px;background:#2A2A3E}
#ssa-prog .seg.on{background:#7C3AED}
#ssa-prog .step{text-align:center;color:#94A3B8;font-size:12px;padding-bottom:6px}
/* ── section header (_SectionHeader) ── */
h1,h2,h3{font-size:18px!important;font-weight:bold!important;color:#F8FAFC!
 important;text-align:left!important;margin:0 0 16px 0!important}
h1::first-line{}
/* ── AppCard per field group ── */
tr.ssa-row,div.ssa-row{display:block!important;width:100%!important;
 margin:0 0 12px 0!important;padding:16px!important;background:#1E2A4A!
 important;border:1px solid #2A3A6A!important;border-radius:16px!important}
td,th{display:block!important;width:auto!important;text-align:left!important;
 border:none!important;background:transparent!important;color:#94A3B8!
 important;font-size:13px;line-height:1.45;padding:2px 0!important}
.ssa-row>[id$="Prompt"]{display:none!important}
.ssa-row>[id$="Fld"]{display:block!important;width:100%!important;
 float:none!important;text-align:left!important}
/* ── Material floating-label fields ── */
.ssa-matf{position:relative;display:block;margin:2px 0 4px 0}
.ssa-matf>input:not([type=checkbox]):not([type=radio]),.ssa-matf>select,
 .ssa-matf>textarea{
 width:100%!important;min-width:0!important;height:auto!important;
 background:#1A1F35!important;color:#F8FAFC!important;
 border:1px solid #2A3A6A!important;border-radius:12px!important;
 padding:26px 16px 10px 16px!important;font-size:16px!important;margin:0!
 important;outline:none!important;-webkit-appearance:none!important}
.ssa-matl{position:absolute;left:16px;top:7px;font-size:11px;color:#94A3B8;
 pointer-events:none;line-height:1.15;max-width:calc(100% - 32px);
 overflow:hidden;text-overflow:ellipsis;display:-webkit-box;
 -webkit-line-clamp:2;-webkit-box-orient:vertical;white-space:normal}
.ssa-matf>input:focus~.ssa-matl,.ssa-matf>select:focus~.ssa-matl,
 .ssa-matf>textarea:focus~.ssa-matl{color:#A78BFA}
input:focus,select:focus,textarea:focus{border-color:#7C3AED!important;
 box-shadow:inset 0 0 0 1px #7C3AED!important}
option{background:#1A1F35!important;color:#F8FAFC!important}
input[type=checkbox],input[type=radio]{width:auto!important;height:auto!
 important;transform:scale(1.35);margin:6px 10px 6px 2px!important;
 accent-color:#7C3AED}
/* unwrapped inputs keep base look */
input[type=text]:not(.ssa-matf>*){}
/* ── buttons ── */
button{background:transparent!important;color:#CBD5E1!important;border:none!
 important;border-radius:12px!important;padding:8px 10px!important;
 font-size:14px!important;margin:2px!important;width:auto!important}
input[type=submit]{border-radius:12px!important;padding:14px 24px!important;
 font-size:16px!important;font-weight:600!important;margin:0!important;
 width:100%!important;text-transform:none!important}
input[value="Next"]{background:#7C3AED!important;color:#F8FAFC!important;
 border:none!important}
input[value="Back"]{background:transparent!important;color:#7C3AED!important;
 border:1px solid #7C3AED!important}
input[type=submit]:active{filter:brightness(.9)}
a{color:#A78BFA!important;text-decoration:none!important}
b,strong{color:#F8FAFC!important}
label,span,p,li,font{color:#CBD5E1!important}
hr{border:none!important;border-top:1px solid #1E293B!important}
/* ── bottom bar buttons (stay in their ITS form; pinned visually) ── */
input.ssa-bb-back{position:fixed!important;left:20px!important;bottom:20px!
 important;width:calc(50% - 28px)!important;z-index:2147483000!important;
 background:transparent!important;color:#7C3AED!important;
 border:1px solid #7C3AED!important;border-radius:12px!important;
 padding:14px 24px!important;font-size:16px!important;font-weight:600!
 important}
input.ssa-bb-next{position:fixed!important;right:20px!important;bottom:20px!
 important;width:calc(50% - 28px)!important;z-index:2147483000!important;
 background:#7C3AED!important;color:#F8FAFC!important;border:none!
 important;border-radius:12px!important;padding:14px 24px!important;
 font-size:16px!important;font-weight:600!important}
/* ── floating star ── */
#ssa-star{position:fixed;right:16px;bottom:110px;z-index:2147482999;
 width:48px;height:48px;border-radius:50%;background:#1E2A4A;
 border:1px solid #2A3A6A;display:flex;align-items:center;justify-content:center;
 font-size:22px;color:#FFC107;box-shadow:0 0 12px rgba(255,193,7,.4)}
"""


def _build_ui_fix_js():
    """Full My Profile replica: app bar, progress bar, section headers,
    Material floating-label fields in AppCards, Back/Next bottom bar and
    the gold Star FAB. Nodes are only moved WITHIN their own <form>, and
    submit inputs get form=<id> so ITS submission keeps working."""
    # Next: run ITS validation when present, then rewrite the form action
    # view->proc (the WebView truncates gw1proc on native submits; navfix
    # handles this for real navigations, we mirror it here).
    onclick_next = (
        "(function(btn){"
        "try{if(typeof valDynFields==='function'){var ok=valDynFields();"
        "if(ok===false)return false}}catch(e){}"
        "var f=btn.closest?btn.closest('form'):null;"
        "if(f){var a=f.getAttribute('action')||'';"
        "a=a.replace(/(gen\\.gw1pkg\\.gw1)view([^a-zA-Z0-9]|$)/g,'$1proc$2');"
        "f.setAttribute('action',a)}return true})(this)")
    css = json.dumps(_UI_CSS)
    return (
        "(function(){"
        "var s=document.getElementById('ssa-dark');"
        "if(!s){s=document.createElement('style');s.id='ssa-dark';"
        "document.head.appendChild(s);}"
        "if(!document.querySelector('meta[name=viewport]')){"
        "var m=document.createElement('meta');m.name='viewport';"
        "m.content='width=device-width,initial-scale=1';"
        "document.head.appendChild(m)}"
        "var vm=document.querySelector('meta[name=viewport]');"
        "vm.setAttribute('content','width=device-width,initial-scale=1,"
        "minimum-scale=1,maximum-scale=1,user-scalable=no');"
        "var vm2=vm.cloneNode(true);vm.parentNode.replaceChild(vm2,vm);"
        "var ab=document.getElementById('ssa-appbar');"
        "if(!ab){ab=document.createElement('div');ab.id='ssa-appbar';"
        "ab.innerHTML='<span>Complete Your Profile</span>';"
        "document.body.insertBefore(ab,document.body.firstChild)}"
        "var pg=document.getElementById('ssa-prog');"
        "if(!pg){pg=document.createElement('div');pg.id='ssa-prog';"
        "var pcode='';"
        "try{pcode=document.querySelector('input[name*=age]').value||''}catch(e){}"
        "var map=['ITS_OAP_START','ITS_OAP02','ITS_OAP03','ITS_OAP04','ITS_OAP05'];"
        "var cur=0;for(var i=0;i<map.length;i++)if(pcode.indexOf(map[i])>=0)cur=i+1;"
        "if(cur===0)cur=pcode?1:1;"
        "var h='<div class=bar>';"
        "for(var i=0;i<5;i++)h+='<div class=\"seg'+(i<cur?' on':'')+'\"></div>';"
        "h+='</div><div class=step>Step '+cur+' of 5</div>';"
        "pg.innerHTML=h;document.body.insertBefore(pg,ab.nextSibling)}"
        "var cards=0,flds=0;"
        "var gs=document.querySelectorAll('div[id$=\"Grp\"]');"
        "for(var gi=0;gi<gs.length;gi++){var g=gs[gi];"
        "var vis=g.querySelectorAll('input:not([type=hidden]),select,textarea');"
        "if(vis.length===0)continue;"
        "if(!g.classList.contains('ssa-row')){g.classList.add('ssa-row');cards++;}"
        "var prompt=g.querySelector('[id$=\"Prompt\"]');"
        "var lt='';"
        "if(prompt){var cl=prompt.cloneNode(true);"
        "cl.querySelectorAll('script').forEach(function(x){x.remove()});"
        "lt=cl.textContent.replace(/\\s+/g,' ').trim();}"
        "for(var vi=0;vi<vis.length;vi++){var c=vis[vi];"
        "var t=(c.type||'').toLowerCase();"
        "if(t==='submit'||t==='button'||t==='image'||t==='reset')continue;"
        "if(c.parentElement&&c.parentElement.classList.contains('ssa-matf'))continue;"
        "if(t==='checkbox'||t==='radio'||c.tagName==='SELECT'&&false){continue}"
        "var w=document.createElement('div');w.className='ssa-matf';"
        "c.parentNode.insertBefore(w,c);w.appendChild(c);flds++;"
        "var mv=(c.getAttribute('mandatory')||'').toUpperCase()==='Y';"
        "if(mv&&!/\\*$/.test(lt)){lt+=' *';}"
        "var lab=document.createElement('label');lab.className='ssa-matl';"
        "lab.textContent=lt||c.name||'';"
        "w.appendChild(lab);}"
        "if(prompt)prompt.style.display='none'}"
        "document.querySelectorAll('.ssa-matl').forEach(function(l){"
        "var tx=l.textContent"
        ".replace(/^[A-Za-z0-9_]+_prmt\\(\\);\\s*/,'')"
        ".replace(/\\s+/g,' ').trim();l.textContent=tx});"
        "document.querySelectorAll('input[type=submit]')"
        ".forEach(function(b){var v=(b.value||'').trim();"
        "if(v==='Next'){b.classList.add('ssa-bb-next')}"
        "else if(v==='Back'){b.classList.add('ssa-bb-back')}});"
        "var oldbb=document.getElementById('ssa-bbar');"
        "if(oldbb)oldbb.parentNode.removeChild(oldbb);"
        "var nfld=document.getElementById('oapNextBtn2Fld');"
        "if(nfld&&!document.getElementById('oapNextBtn2')){"
        "var nb=document.createElement('input');"
        "nb.type='submit';nb.id='oapNextBtn2';nb.name='oapNextBtn2';"
        "nb.value='Next';nb.className='ssa-bb-next';"
        "var nform=nfld.closest?nfld.closest('form'):null;"
        "if(nform&&nform.id)nb.setAttribute('form',nform.id);"
        "nb.setAttribute('onclick'," + json.dumps(onclick_next) + ");"
        "nfld.appendChild(nb)}"
        "var bfld=document.getElementById('oapBackBtn2Fld');"
        "if(bfld&&!document.getElementById('oapBackBtn2')){"
        "var bb=document.createElement('input');"
        "bb.type='button';bb.id='oapBackBtn2';bb.value='Back';"
        "bb.className='ssa-bb-back';"
        "bb.setAttribute('onclick','history.back();return false');"
        "bfld.appendChild(bb)}"
        "if(!document.getElementById('ssa-star')){"
        "var st=document.createElement('div');st.id='ssa-star';"
        "st.textContent='★';document.body.appendChild(st)}"
        "s.textContent=" + css + ";"
        "return 'MY-PROFILE REPLICA ON ('+cards+' cards,'+flds+' fields)'})()"
    )


def _build_postal_picker_js(profile_json):
    """Extract the app's buildPostalCodePickerScript template and inject the
    profile so it auto-picks the saved postal code with correct ITS events.
    The template's db is Pretoria-only, so codes outside it never auto-applied
    (hit=null); we append a direct-apply pass mirroring pick() for any code."""
    dart = open(AUTOFILL_DART_PATH, encoding="utf-8").read()
    m = re.search(r"String buildPostalCodePickerScript\(String profileJson\) \{"
                  r"\s*return '''(.*?)''';", dart, re.DOTALL)
    if not m:
        raise RuntimeError("postal picker template not found")
    tpl = _dart_unescape(m.group(1))
    prof = json.loads(profile_json)
    pc = str(((prof.get("address") or {}).get("postalCode")) or "").strip()
    apply_js = (
        "(function(){var PC=" + json.dumps(pc) + ";if(!PC)return 'NO-CODE';"
        "function apply(id){var v=document.getElementById(id);if(!v)return false;"
        "v.removeAttribute('readonly');v.removeAttribute('disabled');v.value=PC;"
        "var d=document.getElementById(id+'_display');"
        "if(d){d.removeAttribute('readonly');d.removeAttribute('disabled');d.value=PC;}"
        "var ds=document.getElementById(id+'_desc');"
        "if(ds){ds.removeAttribute('readonly');ds.removeAttribute('disabled');ds.value=PC;}"
        "['input','change','blur','focus'].forEach(function(ev){"
        "v.dispatchEvent(new Event(ev,{bubbles:true}));"
        "if(d)d.dispatchEvent(new Event(ev,{bubbles:true}));});return true}"
        "var n=0;"
        "function go(){n=0;"
        "['oapStreetAddrPCodeRq','oapPostalAddrPCodeRq'].forEach(function(id){"
        "var e=document.getElementById(id);"
        "if(e&&!e.value&&apply(id))n++;});"
        "if(n>0)setTimeout(go,800)}"
        "go();"
        "setTimeout(function(){"
        "var sv=document.getElementById('oapStreetAddrPCodeRq');"
        "var sd=document.getElementById('oapStreetAddrPCodeRq_desc');"
        "var pv=document.getElementById('oapPostalAddrPCodeRq');"
        "var pd=document.getElementById('oapPostalAddrPCodeRq_desc');"
        "if(sv&&pv){var V=sv.value,D=sd?sd.value:'';"
        "if(/^[0-9]+$/.test(V)){V=PC;D=PC}"
        "pv.removeAttribute('readonly');pv.removeAttribute('disabled');"
        "pv.value=V;"
        "if(pd){pd.removeAttribute('readonly');pd.removeAttribute('disabled');"
        "pd.value=D;}"
        "['input','change','blur','focus'].forEach(function(ev){"
        "pv.dispatchEvent(new Event(ev,{bubbles:true}));"
        "if(pd)pd.dispatchEvent(new Event(ev,{bubbles:true}));})}},1500);"
        "return 'POSTAL-APPLY '+JSON.stringify(PC)})()"
    )
    return tpl.replace("$profileJson", profile_json) + "\n" + apply_js


def _run_profile_autofill():
    """Pull the real profile from the phone and run the app's autofill engine."""
    pj, err = _pull_profile_json()
    if not pj:
        return 500, {"error": "AUTOFILL FAILED: " + err}
    try:
        prof = json.loads(pj)
    except Exception as e:
        return 500, {"error": f"AUTOFILL FAILED: bad profile JSON: {e}"}

    per = prof.get("personal") or {}
    dem = prof.get("demographic") or {}
    nok = prof.get("nextOfKin") or {}
    addr = prof.get("address") or {}
    con = prof.get("contact") or {}

    title = (per.get("title") or "").strip().upper()
    pc = (addr.get("postalCode") or "").strip()
    paddr = (addr.get("postalAddress") or addr.get("address") or "").strip()
    extra = {
        "OAPTITLE":       title if title in ("MR", "MRS", "MS", "DR",
                                             "PROF", "REV") else "",
        "OAPINITIALS":    (per.get("initials") or "").strip(),
        "OAPSURNAME":     (per.get("lastName") or "").strip(),
        "OAPFIRSTNAMES":  (per.get("firstName") or "").strip(),
        "OAPNAME":        (per.get("firstName") or "").strip(),
        "OAPMAIDEN":      (per.get("maidenName") or "").strip(),
        "OAPIDNUMBER":    (per.get("idNumber") or "").strip(),
        # ── contact ──
        "OAPSACELL":      (con.get("phone") or "").strip(),
        "OAPWORKPHONE":   (con.get("workPhone") or "").strip(),
        "ITSEMAIL":       (con.get("email") or "").strip(),
        "VERIFYEMAIL":    (con.get("verifyEmail")
                           or con.get("email") or "").strip(),
        # ── street address ──
        "OAPSTREETADDR1": (addr.get("address") or "").strip(),
        "OAPSTREETADDR2": (addr.get("addressLine2") or "").strip(),
        "OAPSTREETADDR3": (addr.get("addressLine3") or "").strip(),
        "OAPSTREETADDRPCODEREQ":     pc,
        "OAPSTREETADDRPCODEREQ_DESC": pc,
        # ── postal address ──
        "OAPPOSTALADDR1": paddr,
        "OAPPOSTALADDRPCODEREQ":     pc,
        "OAPPOSTALADDRPCODEREQ_DESC": pc,
        # ── demographics / guardian ──
        "OAPMARITALSTATUS": (dem.get("maritalStatus") or "").strip(),
        "OAPHOMELANG":    (dem.get("homeLanguage") or "").strip(),
        "OAPGUARDNAME":   (nok.get("name") or "").strip(),
        "OAPGUARDCELL":   (nok.get("mobilePhone")
                           or nok.get("phone") or "").strip(),
        "OAPGUARDEMAIL":  (nok.get("email") or "").strip(),
    }

    try:
        js = _build_profile_autofill_js(pj, extra)
    except Exception as e:
        return 500, {"error": f"AUTOFILL FAILED: {e}"}
    # After doAutofill(), report which key fields now hold values.
    verify = ("try{var v=[];"
              "['oapTitle','oapInitials','oapSurname','oapFirstNames',"
              "'oapGender','oapBirthdate','oapCitizenType',"
              "'oapSACell','itsEmail','verifyEmail',"
              "'oapStreetAddrPCodeRq','oapPostalAddrPCodeRq']"
              ".forEach(function(n){var e=document.getElementById(n)"
              "||document.querySelector('[name=\"'+n+'\"]');"
              "if(e)v.push(n+'='+String(e.value).slice(0,20))});"
              "return 'FILLED '+v.length+' | '+v.join(' | ')}"
              "catch(e){return 'done'}")
    if js.strip().endswith("})();"):
        js = js[:js.rfind("})();")] + verify + "\n})();"
    else:
        js = js + "\n" + verify
    # Apply the dark mobile UI first, then the fill, then the postal picker;
    # combine replies. The picker applies itself ~600ms later, so we re-read
    # the two postal fields afterwards.
    s1, p1 = _run_cdp_js(_build_ui_fix_js())
    s2, p2 = _run_cdp_js(js)
    s3, p3 = _run_cdp_js(_build_postal_picker_js(pj))
    time.sleep(2.0)
    check_js = ("(function(){function g(n){var e=document.getElementById(n)"
                "||document.querySelector('[name=\"'+n+'\"]');"
                "return e?String(e.value||''):'-'}"
                "return 'street='+g('oapStreetAddrPCodeRq')"
                "+' postal='+g('oapPostalAddrPCodeRq')"
                "+' desc='+g('oapStreetAddrPCodeRq_desc')})()")
    s4, p4 = _run_cdp_js(check_js)
    ui = (p1 or {}).get("result") if s1 == 200 else "ui-skip"
    fill = (p2 or {}).get("result") if s2 == 200 else (p2 or {}).get("error")
    post = (p4 or {}).get("result") if s4 == 200 else "postal-skip"
    body = f"{ui} | {fill} | {post}" if fill is not None else str(ui)
    return min(s1, s3) if fill is None or s2 != 200 else s2, {"result": body}


def _format_device_result(status, payload):
    if status == 200:
        val = payload.get("result")
        out = str(val) if val not in (None, "") else json.dumps(payload)[:400]
    else:
        out = "ERROR: " + str(payload.get("error", payload))[:300]
    print(f"🎯 Device result: {out[:120]}")
    return out


def _strip_conversational_tail(text):
    """Remove trailing conversational phrases that are not part of the command."""
    tails = [
        r'\s+and\s+tell\s+me\s+what\s+you\s+see\b',
        r'\s+and\s+tell\s+me\s+the\s+text\s+on\s+it\b',
        r'\s+and\s+show\s+me\b',
        r'\s+and\s+describe\s+it\b',
        r'\s+and\s+read\s+it\b',
        r'\s+please\b',
        r'\s+thanks\b',
        r'\s+thank\s+you\b',
    ]
    lowered = text.lower()
    for tail in tails:
        m = re.search(tail, lowered)
        if m:
            return text[:m.start()].rstrip()
    return text


def _run_device_line(line):
    """Parse and execute ONE command line. Returns reply string or None."""
    # Prose guard: long sentences are conversation, not commands — unless the
    # line actually starts with a command keyword.
    if len(line.split()) > 9 and not re.match(
            r'^(fill|click|press|tap|js\s*:|autofill|auto\s*fill|screenshot|ui_dump|dump\s+ui|find|search|edit|run|cmd|shell)\b',
            line, re.IGNORECASE):
        return None
    if re.search(r'\b(?:auto\s*fill|autofill|fill\s+from\s+(?:my\s+)?profile)\b',
                 line, re.IGNORECASE):
        return _format_device_result(*_run_profile_autofill())
    if re.search(r'\b(fix\s+(?:the\s+)?ui|dark(?:en)?(?:\s+mode)?|'
                 r'theme|mobile\s+view|fit\s+screen)\b', line, re.IGNORECASE):
        return _format_device_result(*_run_cdp_js(_build_ui_fix_js()))
    m_fill = re.search(
        r'\bfill\s+([A-Za-z_]\w*)\s+(?:with|to)\s+["\']?(.+?)["\']?[.!]?\s*$',
        line, re.IGNORECASE)
    if m_fill:
        return _format_device_result(*_run_cdp_js(
            _build_fill_js(m_fill.group(1), m_fill.group(2))))
    m_raw = re.search(r'\bjs\s*:\s*(.+)$', line, re.IGNORECASE)
    if m_raw:
        return _format_device_result(*_run_cdp_js(m_raw.group(1).strip()))
    if re.match(r'^(?:list|show|dump)\s+(?:the\s+)?(?:form\s+)?fields\b'
                r'|^form\s+dump$|^what\s+fields', line, re.IGNORECASE):
        return _format_device_result(*_run_cdp_js(FORM_DUMP_JS))
    m_click = re.search(
        r'\b(?:click|press|tap)(?:\s+the)?\s+["\']?(.+?)["\']?\s*(?:button|btn)?[.!]?\s*$',
        line, re.IGNORECASE)
    if m_click:
        return _format_device_result(*_run_cdp_js(
            _build_click_js(m_click.group(1))))
    m_edit = re.search(
        r'\bedit\s+(?:file\s+)?(.+?)\s+replace\s+["\']?(.+?)["\']?\s+with\s+["\']?(.+?)["\']?\s*$',
        line, re.IGNORECASE)
    if m_edit:
        path = m_edit.group(1).strip()
        old_text = m_edit.group(2)
        new_text = m_edit.group(3)
        return _handle_edit_file(path, old_text, new_text)
    m_run = re.search(r'\b(?:run|cmd|shell)\s+(.+)$', line, re.IGNORECASE)
    if m_run:
        cmd = m_run.group(1).strip()
        return _handle_pc_run_command(cmd)
    if re.search(r'\bui_dump\b.*\blook\b.*\bfor\b', line, re.IGNORECASE):
        pics = os.path.join(os.path.expanduser('~'), 'Pictures')
        if not os.path.isdir(pics):
            pics = os.path.expanduser('~')
        m_query = re.search(r'\blook\s+for\s+["\']?(.+?)["\']?\s*$', line, re.IGNORECASE)
        raw_query = m_query.group(1) if m_query else ''
        query = _strip_conversational_tail(raw_query)
        wants_text = bool(re.search(r'\b(text|words|read|say|what\s+does\s+it\s+say)\b', line, re.IGNORECASE))
        return ui_dump_and_search(pics, query, wants_text)
    if re.search(r'\b(?:ui_dump|screenshot|dump\s+ui|screen\s+dump)\b', line, re.IGNORECASE):
        try:
            shot = take_screenshot()
            _add_step("ui_dump", "work", "Screenshot captured", "📸", "done")
            _add_step("ui_dump", "work", "Reading screen…", "👁️", "running")
            text = ''
            try:
                text = ocr_image(shot)
            except Exception:
                pass
            cleaned = _clean_ocr_text(text)
            _add_step("ui_dump", "work", "Summarizing…", "📝", "running")
            _add_step("ui_dump", "work", "Done", "✅", "done")
            if cleaned:
                summary = _summarize_screen_text(cleaned)
                return summary
            return "I couldn't read any text from the screen."
        except Exception as e:
            return f"Screenshot failed: {e}"
    m_find = re.search(
        r'\b(?:find|search)\s+(?:for\s+)?["\']?(.+?)["\']?\s+(?:in|inside)\s+["\']?(.+?)["\']?[.!]?\s*$',
        line, re.IGNORECASE)
    if m_find:
        query = _strip_conversational_tail(m_find.group(1))
        folder = m_find.group(2)
        if not os.path.isdir(folder):
            return f"Folder not found: {folder}"
        matches = search_local_files(folder, query)
        if matches:
            return f"Found {len(matches)} match(es):\n" + "\n".join(matches[:20])
        return f"No files matching '{query}' in {folder}"
    if re.search(r'\b(?:find|search)\s+(?:in\s+)?(?:this\s+pc\s+)?pictures\b', line, re.IGNORECASE):
        pics = os.path.join(os.path.expanduser('~'), 'Pictures')
        if not os.path.isdir(pics):
            return "Pictures folder not found."
        matches = search_local_files(pics, '')
        return f"Pictures folder contains {len(matches)} file(s).\n" + "\n".join(matches)
    return None


def _device_command_reply(user_message):
    """Process a message as a batch of device command lines (one per line).
    Returns combined reply if ANY line was a command, else None."""
    replies = []
    for raw_line in user_message.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        stripped = re.sub(r'^acesi[\s,:;\u2014-]*', '', line,
                          flags=re.IGNORECASE).strip()
        if stripped:
            line = stripped
        result = _run_device_line(line)
        if result is not None:
            replies.append(result)
    if not replies:
        return None
    return "\n".join(replies)

def _run_cdp_js(js_code, device_id=None, target_url=None):
    """Execute JS inside the device WebView. Returns (http_status, payload)."""
    ws = _cdp_connect(device_id, target_url)
    if not ws:
        return 500, {"error": "Failed to connect to CDP. Ensure:\n1. Device is connected via ADB\n2. WebView debugging is enabled\n3. Chrome is running on device"}
    try:
        targets_resp = _cdp_send(ws, "Target.getTargets")
        infos = targets_resp.get("result", {}).get("targetInfos", [])
        pages = [t for t in infos if t.get("type") == "page"]
        if target_url:
            matched = [t for t in pages
                       if t.get("url", "").startswith(target_url)]
            pages = matched or pages
        if not pages:
            return 500, {"error": "Connected to WebView but found no page "
                                  "targets. Open the portal screen in the "
                                  "app first.",
                         "raw_cdp_response": str(targets_resp)[:600]}
        attach = _cdp_send(ws, "Target.attachToTarget", {
            "targetId": pages[0]["targetId"],
            "flatten": True
        })
        session_id = attach.get("result", {}).get("sessionId")
        if not session_id:
            return 500, {"error": f"Failed to attach to page target: {attach}"}
        result = _cdp_js_inject(ws, js_code, session_id)
        if "error" in result:
            return 500, {"error": f"JS execution error: {result['error']}"}
        exc = result.get("result", {}).get("exceptionDetails")
        if exc:
            return 500, {"error": "Page-side JS exception",
                         "exception": str(exc)[:500]}
        return 200, {
            "success": True,
            "result": result.get("result", {}).get("result", {}).get("value"),
        }
    except Exception as e:
        return 500, {"error": f"JS injection failed: {str(e)}"}
    finally:
        try:
            ws.close()
        except:
            pass


@app.route('/js_inject', methods=['POST'])
def js_inject():
    """
    Inject JavaScript into the WebView via CDP.

    Expected JSON body:
    {
        "device_id": "optional_device_serial",
        "javascript": "string of JS code to execute",
        "target_url": "optional URL to filter which page to inject into"
    }
    """
    data = request.json
    if not data or 'javascript' not in data:
        return jsonify({"error": "Missing 'javascript' field"}), 400
    status, payload = _run_cdp_js(
        data['javascript'],
        device_id=data.get('device_id'),
        target_url=data.get('target_url'))
    return jsonify(payload), status


@app.route('/autofill', methods=['POST'])
def autofill():
    """Fill the portal form from the phone's real StudentProfile (Hive)."""
    status, payload = _run_profile_autofill()
    return jsonify(payload), status


@app.route('/ui_fix', methods=['POST'])
def ui_fix():
    """Apply dark mobile-fit theme to the portal WebView."""
    status, payload = _run_cdp_js(_build_ui_fix_js())
    return jsonify(payload), status


@app.route('/edit_file', methods=['POST'])
def edit_file():
    data = request.json
    file_path = data.get('file_path', '')
    content = data.get('content', '')
    if not file_path:
        return jsonify({"error": "Missing file_path"}), 400
    try:
        abs_path = os.path.abspath(file_path)
        sensitive, pattern = _check_file_access_security(abs_path)
        if sensitive:
            _security_alert("sensitive_file_access", f"Pattern: {pattern}, Path: {abs_path}")
            return jsonify({"error": f"Access blocked: sensitive file pattern '{pattern}'"}), 403
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"success": True, "path": abs_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/run_command', methods=['POST'])
def pc_run_command():
    data = request.json
    command = data.get('command', '')
    if not command:
        return jsonify({"error": "Missing command"}), 400
    suspicious, pattern = _check_command_security(command)
    if suspicious:
        _security_alert("suspicious_command", f"Pattern: {pattern}, Command: {command[:200]}")
        return jsonify({"error": f"Command blocked: suspicious pattern '{pattern}'"}), 403
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.abspath(os.path.dirname(__file__))
        )
        return jsonify({
            "success": True,
            "stdout": result.stdout[-4000:] if result.stdout else "",
            "stderr": result.stderr[-2000:] if result.stderr else "",
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timed out after 300 seconds"}), 408
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/memory/all', methods=['GET'])
def memory_all():
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute('SELECT key, value, updated FROM memory')
    rows = c.fetchall()
    conn.close()
    memory = {}
    for key, value, updated in rows:
        memory[key] = {"value": value, "updated": updated}
    return jsonify({"memory": memory})


@app.route('/memory/set', methods=['POST'])
def memory_set():
    data = request.json
    key = data.get('key', '')
    value = data.get('value', '')
    if not key:
        return jsonify({"error": "Missing key"}), 400
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO memory (key, value, updated) VALUES (?, ?, ?)',
              (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route('/memory/forget', methods=['POST'])
def memory_forget():
    data = request.json
    key = data.get('key', '')
    if not key:
        return jsonify({"error": "Missing key"}), 400
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute('DELETE FROM memory WHERE key = ?', (key,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route('/memory/bulk', methods=['POST'])
def memory_bulk():
    data = request.json
    items = data.get('items', {})
    if not items:
        return jsonify({"error": "No items provided"}), 400
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    for key, value in items.items():
        c.execute('INSERT OR REPLACE INTO memory (key, value, updated) VALUES (?, ?, ?)',
                  (key, value, now))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "count": len(items)})


@app.route('/security/test_alert', methods=['POST'])
def security_test_alert():
    _security_alert("test_alert", "This is a test notification from ACEsi security system.")
    return jsonify({"success": True, "message": "Test alert sent"})


@app.route('/security/status', methods=['GET'])
def security_status():
    with _security_lock:
        return jsonify(dict(_security_state))


@app.route('/check-portal', methods=['GET'])
def check_portal():
    target_url = request.args.get('url', 'https://univenierp01.univen.ac.za')
    try:
        start = time.time()
        resp = requests.get(
            target_url,
            timeout=10,
            allow_redirects=True,
            verify=False,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        elapsed = round((time.time() - start) * 1000)
        if resp.status_code < 400:
            return jsonify({
                "status": "up",
                "http_code": resp.status_code,
                "latency_ms": elapsed,
                "detail": f"{resp.status_code} in {elapsed}ms"
            })
        return jsonify({
            "status": "degraded",
            "http_code": resp.status_code,
            "latency_ms": elapsed,
            "detail": f"HTTP {resp.status_code}"
        })
    except requests.exceptions.ConnectionError as e:
        return jsonify({"status": "down", "detail": "Connection refused or host unreachable", "error": str(e)})
    except requests.exceptions.Timeout:
        return jsonify({"status": "down", "detail": "Request timed out"})
    except Exception as e:
        return jsonify({"status": "down", "detail": str(e)})


# ──────────────────────────────────────────────────────────────
# Frontend compatibility endpoints
# ──────────────────────────────────────────────────────────────

@app.route('/notifications/pending', methods=['GET'])
def notifications_pending():
    after = request.args.get('after', '0')
    return jsonify({"notifications": [], "after": after})

@app.route('/opencode/status', methods=['GET'])
def opencode_status():
    with _status_lock:
        return jsonify(dict(_status))

@app.route('/devices', methods=['GET'])
def devices():
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split('\n')
        devices = []
        for line in lines:
            line = line.strip()
            # Real device rows look like "SERIAL\tdevice"; skip headers/blank lines
            if '\t' in line and line.endswith('device'):
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({'id': parts[0], 'status': parts[1]})
        return jsonify({'devices': devices})
    except Exception as e:
        return jsonify({'devices': [], 'error': str(e)})

@app.route('/agents', methods=['GET'])
def agents():
    return jsonify({'agents': []})

# ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # use_reloader=False: the reloader's restart path can deadlock on the
    # CDP/notification daemon threads ("Fatal Python error: _enter_buffered_busy").
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False,
            threaded=True)