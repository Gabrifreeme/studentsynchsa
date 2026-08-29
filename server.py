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
import urllib.parse
import winsound
import subprocess
import time
import tempfile
import threading
import ctypes
from ctypes import wintypes
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
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (
        name TEXT PRIMARY KEY,
        display_name TEXT,
        created TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedule_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT,
        command TEXT,
        schedule_type TEXT,
        time_value TEXT,
        interval_seconds INTEGER,
        enabled INTEGER DEFAULT 1,
        last_run TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS file_watches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT,
        label TEXT,
        restart BOOLEAN DEFAULT 0,
        last_mtime REAL
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


def _open_folder_foreground(path):
    """Open a folder in Explorer and bring its window to the foreground.

    A background process (like Flask) cannot normally steal focus, so merely
    calling os.startfile() just flashes the taskbar. We open the folder with
    os.startfile (which creates the Explorer window titled by its basename),
    then attach our thread's input queue to the current foreground thread and
    call ShowWindow/BringWindowToTop/SetForegroundWindow on the matching
    CabinetWClass window so it comes to the front instead of flashing.
    """
    import win32gui
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Launch a NEW Explorer window at the folder via explorer.exe. This is far
    # more reliable than os.startfile() for actually bringing a folder to the
    # front (os.startfile can reuse an existing/background window or fail to
    # surface known shell folders like Pictures).
    try:
        subprocess.Popen(['explorer.exe', os.path.normpath(path)])
    except Exception as e:
        print(f"⚠️ explorer.exe launch failed ({e}); falling back to os.startfile")
        os.startfile(path)
    # Give Explorer a moment to create the window.
    time.sleep(1.5)

    SW_RESTORE = 9
    SW_SHOWNORMAL = 1
    base = os.path.basename(os.path.normpath(path)).lower()

    # Collect matching visible Explorer windows, preferring the topmost one.
    candidates = []

    def handler(hwnd, _):
        try:
            if win32gui.GetClassName(hwnd) == "CabinetWClass" and win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if base in title.lower():
                    candidates.append((hwnd, title))
        except Exception:
            pass
        return True

    win32gui.EnumWindows(handler, None)
    if not candidates:
        print("⚠️ No matching Explorer window found; folder opened plainly.")
        return

    hwnd, title = candidates[0]
    h_fore = user32.GetForegroundWindow()
    t_cur = kernel32.GetCurrentThreadId()
    t_fore = user32.GetWindowThreadProcessId(h_fore, None) if h_fore else 0

    attached = False
    try:
        if h_fore and t_fore != t_cur:
            attached = bool(user32.AttachThreadInput(t_cur, t_fore, True))
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.ShowWindow(hwnd, SW_SHOWNORMAL)
    finally:
        if attached:
            user32.AttachThreadInput(t_cur, t_fore, False)
    print(f"🖥️ Activated Explorer window ({title!r}, hwnd={hwnd:#x})")

# ──────────────────────────────────────────────────────────────
# Email / Thunderbird helpers
# ──────────────────────────────────────────────────────────────
TB_EXE = r"C:\Program Files\Mozilla Thunderbird\thunderbird.exe"

def _tb_path() -> str:
    """Return the Thunderbird executable path if found."""
    if os.path.exists(TB_EXE):
        return TB_EXE
    # Fallback search
    for root in (r"C:\Program Files", r"C:\Program Files (x86)", os.path.join(os.environ.get("LOCALAPPDATA", ""), "Thunderbird")):
        cand = os.path.join(root, "thunderbird.exe")
        if os.path.exists(cand):
            return cand
    return TB_EXE

EMAILS_CONFIG = os.path.join(os.path.dirname(__file__), "emails.json")
EMAIL_NOTIFY_CONFIG = os.path.join(os.path.dirname(__file__), "email_notify_rules.json")
_EMAIL_SEEN = set()

def _load_email_config() -> dict:
    """Load email credentials from emails.json (for direct IMAP)."""
    if os.path.exists(EMAILS_CONFIG):
        try:
            with open(EMAILS_CONFIG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _load_email_notify_rules() -> list:
    if os.path.exists(EMAIL_NOTIFY_CONFIG):
        try:
            with open(EMAIL_NOTIFY_CONFIG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('rules', [])
        except Exception:
            pass
    return []

def _save_email_notify_rules(rules: list):
    try:
        with open(EMAIL_NOTIFY_CONFIG, 'w', encoding='utf-8') as f:
            json.dump({'rules': rules}, f, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save email notify rules: {e}")

def _email_matches_rule(msg, rule: dict) -> bool:
    """Check if an email message matches a notification rule."""
    if rule.get('account') == 'gmail' and 'gmail' not in rule.get('account', ''):
        pass
    # From
    if rule.get('from'):
        frm = (msg.get('From') or '').lower()
        if rule['from'].lower() not in frm:
            return False
    # Subject
    if rule.get('subject'):
        subj = (msg.get('Subject') or '').lower()
        if rule['subject'].lower() not in subj:
            return False
    # Body
    if rule.get('body'):
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode(errors='replace')
                        break
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode(errors='replace')
            except Exception:
                body = ''
        if rule['body'].lower() not in body.lower():
            return False
    return True

def _show_windows_toast(title: str, message: str):
    """Show a Windows toast notification."""
    try:
        import win32gui
        import win32con
        # Use a simple message box as fallback, or try to use Windows 10 toast
        # For simplicity, use a PowerShell toast
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
        $text = $xml.GetElementsByTagName("text")
        $text[0].AppendChild($xml.CreateTextNode("{title.replace('"', '\\"')}")) | Out-Null
        $text[1].AppendChild($xml.CreateTextNode("{message.replace('"', '\\"')}")) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ACEsi").Show($toast)
        '''
        subprocess.Popen(['powershell', '-NoProfile', '-Command', ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def _poll_email_notifications():
    """Background thread: poll IMAP for new emails matching rules."""
    while True:
        try:
            cfg = _load_email_config()
            rules = _load_email_notify_rules()
            enabled_rules = [r for r in rules if r.get('enabled')]
            if not cfg or not enabled_rules:
                time.sleep(60)
                continue

            import imaplib
            import email
            from email.header import decode_header

            def _fetch_and_check(account_name: str, host: str, port: int, user: str, app_pwd: str, matching_rules: list):
                if not matching_rules:
                    return
                try:
                    imap = imaplib.IMAP4_SSL(host, port)
                    imap.login(user, app_pwd)
                    imap.select('INBOX')
                    typ, data = imap.search(None, 'UNSEEN')
                    if typ == 'OK':
                        nums = data[0].split()
                        for n in nums:
                            typ, msg_data = imap.fetch(n, '(RFC822)')
                            if typ != 'OK':
                                continue
                            raw = msg_data[0][1]
                            msg = email.message_from_bytes(raw)
                            msg_id = msg.get('Message-ID') or f"{account_name}:{n.decode()}"
                            if msg_id in _EMAIL_SEEN:
                                continue
                            for rule in matching_rules:
                                if _email_matches_rule(msg, rule):
                                    subj = ''
                                    if msg.get('Subject'):
                                        try:
                                            subj = decode_header(msg['Subject'])[0][0]
                                            if isinstance(subj, bytes):
                                                subj = subj.decode(errors='replace')
                                        except Exception:
                                            subj = '(no subject)'
                                    frm = msg.get('From') or ''
                                    title = f"📧 {rule.get('name') or 'Email notification'} ({account_name})"
                                    body = f"From: {frm}\nSubject: {subj}"
                                    _show_windows_toast(title, body)
                                    if rule.get('notifyOnce'):
                                        _EMAIL_SEEN.add(msg_id)
                                    break
                    imap.close()
                    imap.logout()
                except Exception as e:
                    print(f"⚠️ Email notify poll error ({account_name}): {e}")

            # Build rules per account
            gmail_rules = [r for r in enabled_rules if r.get('account') in ('both', 'gmail')]
            yahoo_rules = [r for r in enabled_rules if r.get('account') in ('both', 'yahoo')]

            if gmail_rules and 'gmail' in cfg:
                g = cfg['gmail']
                _fetch_and_check('Gmail', g.get('host', 'imap.gmail.com'), g.get('port', 993), g['user'], g['app_password'], gmail_rules)
            if yahoo_rules and 'yahoo' in cfg:
                y = cfg['yahoo']
                _fetch_and_check('Yahoo', y.get('host', 'imap.mail.yahoo.com'), y.get('port', 993), y['user'], y['app_password'], yahoo_rules)

        except Exception as e:
            print(f"⚠️ Email notification poller error: {e}")
        time.sleep(120)  # poll every 2 minutes

def _email_command_reply(user_lower: str) -> str | None:
    """Handle Thunderbird and direct IMAP commands.
    Returns a reply string if handled, None otherwise.
    """
    # --- Thunderbird launcher / controller ---
    if any(kw in user_lower for kw in ('thunderbird', 'mail client', 'email app')):
        tb = _tb_path()
        if not os.path.exists(tb):
            return "❌ Thunderbird not found at expected path."

        # Compose new mail?
        if any(kw in user_lower for kw in ('compose', 'new mail', 'new email', 'write mail', 'write email')):
            try:
                subprocess.Popen([tb, '-compose'])
                return "📧 Thunderbird opened to compose a new email."
            except Exception as e:
                return f"❌ Failed to launch Thunderbird compose: {e}"

        # Open specific account/folder?
        # "open gmail in thunderbird" / "open yahoo in thunderbird" / "open thunderbird gmail"
        if 'gmail' in user_lower or 'gabrieltrollip200@gmail.com' in user_lower:
            try:
                subprocess.Popen([tb, '-P', 'default-release', '-mail', 'imap://gabrieltrollip200%40gmail.com@imap.gmail.com/INBOX'])
                return "📧 Thunderbird opened to Gmail inbox."
            except Exception as e:
                return f"❌ Failed to open Gmail in Thunderbird: {e}"

        if 'yahoo' in user_lower or 'chris.trollip@yahoo.com' in user_lower:
            try:
                subprocess.Popen([tb, '-P', 'default-release', '-mail', 'imap://chris.trollip%40yahoo.com@imap.mail.yahoo.com/INBOX'])
                return "📧 Thunderbird opened to Yahoo inbox."
            except Exception as e:
                return f"❌ Failed to open Yahoo in Thunderbird: {e}"

        # Default: just launch Thunderbird
        try:
            subprocess.Popen([tb])
            return "📧 Thunderbird launched."
        except Exception as e:
            return f"❌ Failed to launch Thunderbird: {e}"

    # --- Direct IMAP reading (requires emails.json with app passwords) ---
    # Commands: "read my emails", "read my gmail", "read my yahoo",
    #           "check my email", "latest emails", "search my email for ..."
    imap_keywords = ('read my email', 'read my emails', 'read my gmail', 'read my yahoo',
                     'check my email', 'check my emails', 'check gmail', 'check yahoo',
                     'latest email', 'latest emails', 'read gmail', 'read yahoo',
                     'search my email', 'search my emails')
    if any(kw in user_lower for kw in imap_keywords):
        cfg = _load_email_config()
        if not cfg:
            return ("📭 No email config found (emails.json). "
                    "Thunderbird works for browsing; for ACEsi to read/sync emails "
                    "directly, add app passwords to emails.json.")
        try:
            return _imap_read_emails(user_lower, cfg)
        except Exception as e:
            return f"❌ IMAP error: {e}"

    return None

def _imap_read_emails(user_lower: str, cfg: dict) -> str:
    """Fetch recent emails via IMAP for Gmail/Yahoo based on config."""
    import imaplib
    import email
    from email.header import decode_header

    results = []
    max_fetch = 10
    # Determine which accounts to fetch
    fetch_gmail = ('gmail' in user_lower) or ('gabrieltrollip200@gmail.com' in user_lower)
    fetch_yahoo = ('yahoo' in user_lower) or ('chris.trollip@yahoo.com' in user_lower)
    if not fetch_gmail and not fetch_yahoo:
        fetch_gmail = fetch_yahoo = True  # both if unspecified

    def _fetch(account_name: str, host: str, port: int, user: str, app_pwd: str, limit: int = 5):
        try:
            imap = imaplib.IMAP4_SSL(host, port)
            imap.login(user, app_pwd)
            imap.select('INBOX')
            typ, data = imap.search(None, 'ALL')
            if typ != 'OK':
                return [f"⚠️ {account_name}: search failed"]
            nums = data[0].split()
            recent = nums[-limit:] if nums else []
            msgs = []
            for n in reversed(recent):
                typ, msg_data = imap.fetch(n, '(RFC822)')
                if typ != 'OK':
                    continue
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subj = ''
                if msg['Subject']:
                    try:
                        subj = decode_header(msg['Subject'])[0][0]
                        if isinstance(subj, bytes):
                            subj = subj.decode(errors='replace')
                    except Exception:
                        subj = '(undecodable subject)'
                frm = msg['From'] or ''
                date = msg['Date'] or ''
                msgs.append(f"  • [{date}] {frm} — {subj}")
            imap.close()
            imap.logout()
            return [f"📬 {account_name} (last {len(msgs)}):"] + msgs if msgs else [f"📭 {account_name}: no messages"]
        except Exception as e:
            return [f"❌ {account_name} IMAP error: {e}"]

    if fetch_gmail and 'gmail' in cfg:
        g = cfg['gmail']
        results.extend(_fetch('Gmail', g.get('host', 'imap.gmail.com'), g.get('port', 993),
                             g['user'], g['app_password'], limit=max_fetch))
    if fetch_yahoo and 'yahoo' in cfg:
        y = cfg['yahoo']
        results.extend(_fetch('Yahoo', y.get('host', 'imap.mail.yahoo.com'), y.get('port', 993),
                             y['user'], y['app_password'], limit=max_fetch))

    if not results:
        return "📭 No email accounts configured or no messages found."
    return "\n".join(results)

# ──────────────────────────────────────────────────────────────
# Agentic tool loop: lets the cloud model actually CALL tools and narrate
# each call as a live, opencode-style step (read / edit / run / search …).
# The model returns either:
#   a JSON tool block  -> ACEsi executes it, shows the step, appends the
#                         result back into the conversation, and loops;
#   plain text         -> final answer, returned to Chris.
# Bounded iterations so a runaway tool loop can't hang the request.
# ──────────────────────────────────────────────────────────────
TOOL_SCHEMA_TEXT = (
    "\n\nYou have tools. When a task requires them, call ONE tool at a time by "
    "writing EXACTLY a JSON block in this form (nothing else in that message):\n"
    "```tool\n{\"tool\": \"read_file\", \"args\": {\"path\": \"lib/main.dart\"}}\n```\n"
    "Available tools:\n"
    "- read_file (path) — read a file\n"
    "- write_file (path, content) — write a file\n"
    "- edit_file (path, old_text, new_text) — replace exact text\n"
    "- run_command (command) — run a shell/build/test command\n"
    "- search (query) — search the local codebase\n"
    "- web_search (query) — search the web\n"
    "- lint (path) — lint/syntax-check a file\n"
    "- stackoverflow (error) — look up an error on Stack Overflow\n"
    "- memory — read ACEsi's stored memory\n"
    "- sandbox (code) — run generated code safely\n"
    "After each tool result comes back, continue: call the next tool if needed, "
    "otherwise give Chris a concise plain-text summary of what you did.\n"
)


def _parse_tool_call(text):
    """Extract a tool call. Returns (name, args) or None.
    Tolerates several formats:
      <tool_call>{"tool":..., "args":{...}}</tool_call>
      <tool_call>NAME<arg_key>K</arg_key><arg_value>V</arg_value>...</tool_call>
      ```tool {...} ``` / ```jsontool {...} ```
      {"tool":..., "args":{...}}
      TOOL: name {json}
    """
    if not text:
        return None

    # arg_tag style: <tool_call>NAME<arg_key>K</arg_key><arg_value>V</arg_value>...</tool_call>
    m = re.search(r"<tool_call>\s*([A-Za-z_]+)((?:\s*<arg_key>.*?</arg_key>\s*<arg_value>.*?</arg_value>\s*)+)\s*</tool_call>", text, re.S | re.I)
    if m:
        name = m.group(1)
        body = m.group(2)
        args = {}
        for km, vm in re.findall(r"<arg_key>(.*?)</arg_key>\s*<arg_value>(.*?)</arg_value>", body, re.S | re.I):
            args[km.strip()] = vm.strip()
        return name, args

    # JSON-in-tag style.
    m = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", text, re.S | re.I)
    if m:
        block = m.group(1)
    else:
        m = re.search(r"```tool\s*(\{.*?\})\s*```", text, re.S | re.I)
        if not m:
            m = re.search(r"```jsontool\s*(\{.*?\})\s*```", text, re.S | re.I)
        block = m.group(1) if m else None
    if not block:
        m = re.search(r'\{\s*"tool"\s*:\s*"([A-Za-z_]+)"\s*,\s*"args"\s*:\s*(\{.*?\})\s*\}', text, re.S)
        if m:
            block = "{" + m.group(0) + "}"
    if not block:
        # Also accept a bare `TOOL: name {json}` line.
        m = re.search(r'\bTOOL\s*:\s*([A-Za-z_]+)\s*(\{.*?\})', text, re.S | re.I)
        if m:
            block = '{"tool": "' + m.group(1) + '", "args": ' + m.group(2) + '}'
    if not block:
        return None
    try:
        data = json.loads(block)
        return data.get("tool"), data.get("args") or {}
    except Exception:
        return None


def _extract_reply_text(response):
    """Robustly pull the assistant's visible text from an OpenRouter-style
    response, tolerating reasoning models that return reasoning_content
    and a null content. Returns '' if there is nothing usable."""
    try:
        data = response.json()
    except Exception:
        return ""
    # Common shapes: choices[0].message / choices[0] / top-level message
    msg = None
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        msg = first.get("message") if isinstance(first, dict) else None
        if not msg and isinstance(first, dict):
            msg = first
    if msg is None and data.get("message"):
        msg = data["message"]
    if not isinstance(msg, dict):
        return ""
    text = (msg.get("content") or "") if isinstance(msg.get("content"), str) else ""
    if not text:
        for key in ("reasoning_content", "reasoning", "thinking", "output_text"):
            v = msg.get(key)
            if isinstance(v, str) and v.strip():
                text = v
                break
    return text.strip() if text else ""


def _ask_direct_answer(messages):
    """Make a final model call asking for a plain answer with NO tools.
    Returns the text, or '' if it fails."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    }
    prompt_messages = list(messages) + [
        {"role": "user",
         "content": "Give me your final, plain-text answer now. Do NOT call any tools and do NOT "
                    "output a <tool_call>. Reply directly to the user with what you know."},
    ]
    for model_id in [OPENROUTER_MODEL] + [m for m in FALLBACK_MODELS if m != OPENROUTER_MODEL]:
        try:
            resp = requests.post(
                f"{OPENROUTER_ENDPOINT}/chat/completions",
                headers=headers,
                json={"model": model_id, "messages": prompt_messages,
                      "temperature": 0.3, "max_tokens": 600},
                timeout=(10, 60),
            )
            if resp.status_code == 200:
                return _extract_reply_text(resp)
        except Exception:
            continue
    return ""


def _direct_reply(user_message):
    """Answer a normal conversational/informational question with ONE plain
    model call and NO tools at all. Returns the text or '' on failure."""
    system = _recall_context()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    }
    messages = [
        {"role": "system",
         "content": system + ("\n\nReply directly and concisely. Do NOT call any tools, "
                              "do NOT open or read files, do NOT explore the project. "
                              "Just answer the user's question plainly.")},
        {"role": "user", "content": user_message},
    ]
    for model_id in [OPENROUTER_MODEL] + [m for m in FALLBACK_MODELS if m != OPENROUTER_MODEL]:
        try:
            resp = requests.post(
                f"{OPENROUTER_ENDPOINT}/chat/completions",
                headers=headers,
                json={"model": model_id, "messages": messages,
                      "temperature": 0.3, "max_tokens": 600},
                timeout=(10, 60),
            )
            if resp.status_code == 200:
                return _extract_reply_text(resp)
        except Exception:
            continue
    return ""


def _needs_tools(user_message):
    """Return True only when the user explicitly asks for file/code/command/
    device/action work. Ordinary questions fall through to a direct answer."""
    ml = user_message.lower()
    explicit = [
        "read ", "open ", "edit ", "write ", " create file", "fix ", "debug ",
        "run ", "execute", "lint", "search for", "stack overflow", "stackoverflow",
        "semantic", "reindex", "heal", "visual bug", "vm-service", "vm service",
        "auto-fix", "auto fix", "refactor", "make ", "change ", "update the code",
        "device", "screen", "adb", "scrcpy", "tap ", "install ", "launch ",
        "error is:", "analyse the error", "analyze the error", "troubleshoot",
        "investigate", "what's wrong", "is this file", "check the code",
        "review this", "look at ", "show the code", "print the ",
    ]
    for kw in explicit:
        if kw in ml:
            return True
    if ".dart" in ml or ".py" in ml or "lib/" in ml or "server.py" in ml:
        return True
    if re.match(r'^(?:read|open|edit|write|fix|run|show|list)\b', ml):
        return True
    return False


def _agentic_chat(user_message):
    """Run the agentic tool loop. Returns the final plain-text reply."""
    system = _recall_context()
    system = system.replace("You are not a chatbot. You are a presence.",
                            "You are not a chatbot. You are a presence." + TOOL_SCHEMA_TEXT)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    }
    history_for_ui = []
    for iteration in range(6):
        history_for_ui.append(messages)
        _set_status(status="busy", activity=f"Thinking… (step {iteration + 1})")
        _add_step("agent", "work", f"Step {iteration + 1}: working…", "🧠", "running")

        response = None
        for model_id in [OPENROUTER_MODEL] + [m for m in FALLBACK_MODELS if m != OPENROUTER_MODEL]:
            for attempt in range(3):
                try:
                    response = requests.post(
                        f"{OPENROUTER_ENDPOINT}/chat/completions",
                        headers=headers,
                        json={
                            "model": model_id,
                            "messages": messages,
                            "temperature": 0.4,
                            "max_tokens": 700,
                        },
                        timeout=(10, 120),
                    )
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    if attempt < 2:
                        continue
                    return f"Connection to model failed after retries. Please try again."
            if response is not None and response.status_code == 200:
                break
        if response is None or response.status_code != 200:
            _add_step("agent", "work", f"Model error {response.status_code if response else 'none'}", "❌", "error")
            return f"Error: model returned {response.status_code if response else 'no response'}."

        reply = _extract_reply_text(response)
        if not reply:
            # Reasoning-only or empty response from the model; feed a nudge
            # and let the loop (or the fallback model) try again instead of
            # failing the whole turn.
            if iteration < 5:
                _add_step("agent", "work", "Model returned no text, nudging…", "🔁", "running")
                messages.append({"role": "user", "content": "You produced no answer. Please continue and reply now."})
                continue
            return "I couldn't get a clear reply from the model. Try asking again."

        tool_match = _parse_tool_call(reply)
        if tool_match:
            tool, args = tool_match
            _add_step("agent", "work", f"Running {tool}…", "🛠️", "running")
            result = _mcp_dispatch(tool, args)
            outcome = result.get("ok", False)
            icon = "✅" if outcome else "❌"
            label = {
                "read_file": f"read {args.get('path','?')}",
                "write_file": f"write {args.get('path','?')}",
                "edit_file": f"edit {args.get('path','?')}",
                "run_command": f"run {args.get('command','?')}",
                "search": f"search '{args.get('query') or args.get('q','')}'",
                "web_search": f"web search '{args.get('query','')}'",
                "lint": f"lint {args.get('path','?')}",
                "stackoverflow": f"lookup error on Stack Overflow",
                "memory": "read memory",
                "sandbox": "run sandboxed code",
            }.get(tool, tool)
            _add_step(label, "work", label, icon, "done")
            if outcome:
                _add_step("agent", "work", f"Step {iteration + 1}: {tool} done", "✅", "done")
            else:
                _add_step("agent", "work", f"Step {iteration + 1}: {tool} failed: {result.get('error','')}", "⚠️", "error")

            result_text = json.dumps(result, ensure_ascii=False)
            if len(result_text) > 6000:
                result_text = result_text[:6000] + "\n…[truncated]"
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Tool {tool} returned:\n{result_text}"})
            continue  # loop to call the model again

        # Plain text = final answer.
        _add_step("agent", "work", "Done.", "🧠", "done")
        return reply

    # Out of steps: make ONE final call asking for a direct answer (no tools),
    # so the user always gets something useful instead of a dead-end.
    try:
        final = _ask_direct_answer(messages)
    except Exception:
        final = ""
    _add_step("agent", "work", "Done.", "🧠", "done")
    return final or "I ran out of steps before finishing. Here's where things stand — tell me to continue and I will."


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

    # Handle explicit file read/open requests. Deliberately conservative:
    # only match when the message STARTS with an imperative "read"/"open"
    # verb followed by a concrete file/folder target. Never hijack questions
    # or conversational messages (we've regressed on this before).
    global LAST_FILE_PATH
    user_lower = user_message.strip().lower()
    # Strip a leading bot-name prefix so "ACEsi open StudentSyncSA" behaves
    # exactly like "open StudentSyncSA" (routing + open/read matching included).
    user_lower = re.sub(r'^\s*(?:[a]?ce\s*si|acesi|a\.?c\.?e\.?s\.?i|ce\s*si|csi|c\.?s\.?i|hey\s*(?:ace\s*si|ce\s*si)|your\s*name)\b[\s:,.-]*', '', user_lower, flags=re.IGNORECASE).strip()
    is_interrogative = re.match(r'\b(what|whats|when|why|how|which|who|where|is|are|can|could|would|do|does|did|please)\b', user_lower)

    # ── Compound instruction ─────────────────────────────────────────────
    # "open <folder> and <look for|find|show> <target>" → open the folder, then
    # search it for a matching file by name. Enables add-on follow-up actions
    # in a single message (e.g. "ACEsi open My Pictures and look for the meme file").
    compound = re.match(
        r'^(?:open|read|go\s+to|go\s+into|navigate\s+to|locate)\s+(?:the\s+|this\s+)?(?:file\s+)?(.+?)(?:\s+(?:and|abd|aand|&))?\s+(?:look\s+for|find|search\s+for|look\s+up|show)\s+(?:the\s+|a\s+|an\s+)?(.+?)\s*$',
        user_lower,
    )
    if compound and not is_interrogative:
        folder_arg = compound.group(1).strip().strip('"\'')
        folder_arg = re.sub(r'\s+\b(?:file|folder)\b$', '', folder_arg).strip()
        target_arg = compound.group(2).strip().strip('"\'')
        # Strip trailing punctuation.
        target_arg = re.sub(r'[.。!?,\s]+$', '', target_arg).strip()
        # Drop a redundant trailing "and open it (in/on <app>)" — single matches already open.
        target_arg = re.sub(r'\s+(?:and|abd|aand|&)\s+open\s+it(?:\s+(?:in|on|with)\s+[\w. -]+)?$', '', target_arg).strip()
        # Drop a trailing "file"/"folder" word.
        target_arg = re.sub(r'\s+\b(?:file|folder)\b$', '', target_arg).strip()
        home = os.path.expanduser('~')
        shell_map2 = {
            'my pictures': 'Pictures', 'pictures': 'Pictures', 'picture': 'Pictures',
            'my documents': 'Documents', 'documents': 'Documents',
            'my downloads': 'Downloads', 'downloads': 'Downloads',
            'my desktop': 'Desktop', 'desktop': 'Desktop',
            'my music': 'Music', 'music': 'Music',
            'my videos': 'Videos', 'videos': 'Videos',
            'studentsyncsa': 'StudentSyncSA', 'student sync sa': 'StudentSyncSA',
        }
        search_root = None
        fpa = folder_arg.strip().strip('\\/').lower()
        if fpa in shell_map2:
            cand = os.path.join(home, shell_map2[fpa])
        else:
            cand = folder_arg
        if not os.path.isabs(cand):
            for base in ('C:\\Users\\chris\\StudentSyncSA', home, os.path.join(home, 'Documents')):
                b = os.path.join(base, cand)
                if os.path.isdir(b):
                    cand = b
                    break
        if os.path.isdir(cand):
            search_root = cand
        if search_root:
            _set_status(status="busy", activity=f"Searching {search_root}…")
            hits = []
            matches = []
            base_title = os.path.basename(os.path.normpath(search_root)).lower()
            _open_folder_foreground(search_root)
            _add_step("open_folder", "work", f"Opened {search_root}", "🖥️", "done")
            needle = target_arg.lower().replace('file', '').strip()
            for dirpath, dirnames, filenames in os.walk(search_root):
                dirnames[:] = [d for d in dirnames if not d.lower() in ('appdata', '.git', 'node_modules', '$recycle.bin', 'system volume information')]
                for fn in filenames:
                    if needle in fn.lower() or (needle and ' '.join(needle.split()) in ' '.join(fn.lower().replace('_', ' ').replace('-', ' ').split())):
                        full = os.path.join(dirpath, fn)
                        matches.append(full)
                        hits.append(fn)
                    if len(matches) >= 10:
                        break
                if len(matches) >= 10:
                    break
            if matches:
                best = matches[0]
                if len(matches) == 1:
                    # Exactly one match → open the file itself, without the
                    # "Open with" prompt. Images go to the Windows Photos app;
                    # everything else uses the default handler.
                    ext = os.path.splitext(best)[1].lower()
                    opened = False
                    # Clear the Mark-of-the-Web (Zone.Identifier) so Windows
                    # doesn't show the "Is this file from a trusted source?"
                    # prompt before opening it. Run synchronously so the flag is
                    # removed before we open the file.
                    try:
                        subprocess.run(['powershell', '-NoProfile', '-Command', 'Unblock-File -LiteralPath ' + repr(best.replace("'", "''"))], capture_output=True, timeout=15)
                    except Exception:
                        pass
                    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'):
                        try:
                            q = urllib.parse.quote(os.path.normpath(best))
                            subprocess.Popen(['cmd', '/c', 'start', '', f'ms-photos:viewer?fileName={q}'])
                            opened = True
                        except Exception:
                            opened = False
                    if not opened:
                        try:
                            os.startfile(best)
                            opened = True
                        except Exception:
                            opened = False
                    if not opened:
                        try:
                            subprocess.Popen(['explorer.exe', '/select,', os.path.normpath(best)])
                        except Exception:
                            pass
                    print(f"🖥️ Opened file: {best}")
                    _add_step("open_file", "work", f"Opened {best}", "🖥️", "done")
                else:
                    # Multiple matches → reveal the best one in Explorer and list them.
                    try:
                        subprocess.Popen(['explorer.exe', '/select,', os.path.normpath(best)])
                    except Exception:
                        pass
                    print(f"🖥️ Revealed match: {best}")
                    _add_step("find_file", "work", f"Found '{target_arg}' in {search_root}", "🔎", "done")
                _set_status(status="idle", activity="")
                return jsonify({"reply": f"Opened {search_root} in Explorer.\n\nLooking for *{target_arg}* — found {len(matches)} match(es):\n" + "\n".join(f"• {m}" for m in matches)})
            _set_status(status="idle", activity="")
            return jsonify({"reply": f"Opened {search_root} in Explorer.\n\nLooked for *{target_arg}* but no matching file was found."})

    # ── EMAIL / THUNDERBIRD COMMANDS ──────────────────────────────────────
    # Thunderbird controller + direct IMAP (Gmail/Yahoo). App passwords are
    # read from emails.json when present; Thunderbird launching works without.
    _em = user_message.lower()
    _email_reply = _email_command_reply(_em)
    if _email_reply is not None:
        save_conversation("assistant", _email_reply)
        _set_status(status="idle", activity="", last_reply=_email_reply)
        return jsonify({"reply": _email_reply})

    file_read_match = re.match(
        r'^(?:read|open|go\s+to|go\s+into|navigate\s+to|locate)\s+(?:the\s+|this\s+)?(?:file\s+)?(.+?)\s*$',
        user_lower,
    )
    if file_read_match and not is_interrogative:
        is_open = True
        candidate = file_read_match.group(1).strip().strip('"\'')
        candidate = re.sub(r'(?:\s+(?:for\s+me|please|file))$', '', candidate)
        candidate = re.sub(r'\?+$', '', candidate).strip()
        candidate = re.sub(r'^(?:the|this|that)?\s*file\s*:\s*', '', candidate, flags=re.IGNORECASE).strip()
        candidate = re.sub(r'\b(?:in|on)\s+(?:my\s+)?(?:documents|document)\b', '', candidate, flags=re.IGNORECASE)
        candidate = re.sub(r'\bon\s+my\s+computer\b', '', candidate, flags=re.IGNORECASE).strip()
        # Drop trailing context words so "open the StudentSyncSA project" and
        # "open the project in explorer" resolve to the project folder itself.
        candidate = re.sub(r'\b(?:in\s+(?:the\s+)?(?:file\s+)?explorer|in\s+file\s+explorer)\s*$', '', candidate, flags=re.IGNORECASE).strip()
        candidate = re.sub(r'\b(?:project|folder|directory)\s*$', '', candidate, flags=re.IGNORECASE).strip()
        vague = candidate.lower() in ('the', 'it', 'this', 'that', 'file', 'the file', 'this file', 'that file', 'previous', 'last')
        if vague and LAST_FILE_PATH:
            file_path = LAST_FILE_PATH
        elif not vague:
            file_path = candidate
        else:
            file_path = None
    else:
        file_path = None
    # Fallback: an explicit "open...the project" / "open the project in explorer"
    # that resolved to nothing should open the project folder itself.
    if not file_path and not is_interrogative:
        proj_fb = re.match(r'^(?:open|read)\b.+\bproject\b', user_lower)
        if proj_fb:
            file_path = 'C:\\Users\\chris\\StudentSyncSA'
    if file_path:
        COMMON_EXTS = ('.pdf', '.txt', '.png', '.jpg', '.jpeg', '.docx', '.md')
        if not os.path.isabs(file_path):
            doc_base = os.path.join(os.path.expanduser('~'), 'Documents')
            proj_base = 'C:\\Users\\chris\\StudentSyncSA'
            # If the target names the project folder itself (or its basename), open that directly.
            fp_norm = file_path.strip().strip('\\/').lower()
            proj_name = os.path.basename(proj_base).lower()
            # Map common shell-folder names so "open My Pictures" / "open Downloads"
            # resolve to the real user folders instead of falling through to the model.
            shell_map = {
                'my pictures': 'Pictures', 'pictures': 'Pictures', 'pic': 'Pictures',
                'my documents': 'Documents', 'documents': 'Documents', 'docs': 'Documents',
                'my downloads': 'Downloads', 'downloads': 'Downloads', 'download': 'Downloads',
                'my desktop': 'Desktop', 'desktop': 'Desktop',
                'my music': 'Music', 'music': 'Music',
                'my videos': 'Videos', 'videos': 'Videos',
            }
            home = os.path.expanduser('~')
            if fp_norm in shell_map:
                shell_path = os.path.join(home, shell_map[fp_norm])
                if os.path.isdir(shell_path):
                    file_path = shell_path
            if fp_norm == proj_name or fp_norm.replace('\\', '/') == proj_base.replace('\\', '/').lower():
                file_path = proj_base
            # Also match near variants e.g. "studentsyncsa", "studentsync" etc.
            elif proj_name.startswith(fp_norm) and len(fp_norm) >= 5:
                file_path = proj_base
            else:
                doc_path = os.path.join(doc_base, file_path)
                proj_path = os.path.join(proj_base, file_path)
                if os.path.isdir(doc_path) or os.path.isdir(proj_path):
                    file_path = doc_path if os.path.isdir(doc_path) else proj_path
                elif os.path.exists(doc_path):
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
            if os.path.isdir(file_path):
                _open_folder_foreground(file_path)
                print(f"🖥️ Opened folder in Explorer: {file_path}")
                _set_status(status="idle", activity="")
                _add_step("open_folder", "work", f"Opened {file_path}", "🖥️", "done")
                return jsonify({"reply": f"Opened {file_path} in Explorer."})
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
                # "open <file>" should reveal it in Windows Explorer, matching
                # what "open <folder>" does for the enclosing directory.
                if os.path.isdir(file_path):
                    _open_folder_foreground(file_path)
                else:
                    try:
                        subprocess.Popen(['explorer.exe', '/select,', os.path.normpath(file_path)])
                    except Exception as e2:
                        print(f"⚠️ explorer reveal failed: {e2}")
                        os.startfile(file_path)
                print(f"🖥️ Opened in Explorer: {file_path}")
                _set_status(status="idle", activity="")
                _add_step("open_folder", "work", f"Opened {file_path}", "🖥️", "done")
                return jsonify({"reply": f"Opened {file_path} in Explorer."})
            print(f"📖 Read file: {file_path} ({len(content)} chars)")
            _add_step("read_file", "work", f"Read {file_path}", "📖", "done")
            reply = f"Here's the content of `{file_path}`:\n\n```\n{content}\n```"
            reply = _sanitize_response(reply)
            save_conversation("assistant", reply)
            _set_status(status="idle", activity="", last_reply=reply)
            return jsonify({"reply": reply})
        except Exception as e:
            _set_status(status="error", activity="Failed to read file")
            _add_step("read_file", "work", f"Read {file_path}", "📖", "error")
            return jsonify({"reply": f"❌ Could not read file: {e}"})

    # Day-of-week check: "what day is it today" asks for the WEEKDAY,
    # not the calendar date. Answer deterministically via Python.
    _wm = user_message.lower()
    if re.search(r'\bwhat\s+day(?:\s+oftheweek|oftheweek)?\b', _wm.replace(' ', '')) or \
       re.search(r'\bwhat\s+day\s+is\s+(it|today)\b', _wm) or \
       ("day of the week" in _wm) or (_wm.strip() in ("what day is today", "what day is it today", "what day is today?", "what day is it today?")):
        _weekday = datetime.now().strftime("%A")
        _reply = f"It's **{_weekday}** today."
        _reply = _sanitize_response(_reply)
        save_conversation("assistant", _reply)
        _set_status(status="idle", activity="", last_reply=_reply)
        return jsonify({"reply": _reply})

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

    _set_status(activity="Reading message…")
    print(f"📨 Incoming message length: {len(user_message)} chars")
    max_chars = 8000
    if len(user_message) > max_chars:
        user_message = user_message[:max_chars] + "\n\n[Message truncated...]"
        print(f"✂️ Truncated to {max_chars} chars")

    # Ordinary conversational / informational questions get a DIRECT answer
    # with no tools at all — never the agentic loop (which tends to over-explore
    # the project instead of just answering). Only explicit file/code/command
    # requests enter the agentic tool loop.
    if not _needs_tools(user_message):
        print("🧭 Routing to direct answer (no tools).")
        _add_step("agent", "answer", "Answering directly…", "🧠", "running")
        reply = _direct_reply(user_message)
        if not reply:
            reply = "I couldn't produce an answer. Could you rephrase?"
        if _looks_like_dont_know(reply):
            reply = _do_research_and_answer(user_message, reply)
        reply = _sanitize_response(reply)
        save_conversation("assistant", reply)
        _set_status(status="idle", activity="", last_reply=reply)
        return jsonify({"reply": reply})

    # Agentic tool loop: the model can call read/edit/run/search tools,
    # and each call is narrated live as an opencode-style step.
    try:
        reply = _agentic_chat(user_message)
    except Exception as e:
        print(f"💥 Exception in /chat: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        _add_step("call_model", "work", f"Exception: {type(e).__name__}", "💥", "error")
        _set_status(status="error", activity=str(e))
        return jsonify({"reply": f"Error: {str(e)}"})

    if _looks_like_dont_know(reply):
        print("🔎 Reply looks uncertain — triggering research…")
        _add_step("call_model", "work", "Answer uncertain, researching…", "🔎", "running")
        reply = _do_research_and_answer(user_message, reply)
    reply = _sanitize_response(reply)
    save_conversation("assistant", reply)
    _set_status(status="idle", activity="", last_reply=reply)
    return jsonify({"reply": reply})

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
    suspicious, pattern = _check_command_security(command)
    if suspicious:
        _security_alert("suspicious_command", f"Pattern: {pattern}, Command: {command[:200]}")
        return jsonify({'error': f"Command blocked: suspicious pattern '{pattern}'"}), 403
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
# Code Sandbox: run generated Python code in an isolated temp directory.
# - Runs in its own temp dir (can't touch repo files accidentally).
# - Blocks network sockets + dangerous imports so generated code can't
#   phone home or escape the sandbox easily.
# - Hard timeout so runaway loops can't hang AceSI.
# ──────────────────────────────────────────────────────────────
SANDBOX_ALLOWED_IMPORTS = {
    'math', 'random', 'json', 're', 'datetime', 'itertools', 'functools',
    'collections', 'statistics', 'string', 'typing', 'dataclasses',
}

SANDBOX_DANGER_IMPORTS = (
    'import os', 'from os', 'import sys', 'from sys',
    'import subprocess', 'from subprocess',
    'import socket', 'from socket', 'import requests',
    'import urllib', 'from urllib', 'import shutil', 'import pathlib',
    'open(', 'eval(', 'exec(', 'compile(', '__import__',
)


@app.route('/sandbox', methods=['POST'])
def sandbox():
    """
    { "code": "..." }  -> runs code in isolation, returns stdout/stderr/result.
    Code may NOT touch the filesystem, network, or use dangerous imports.
    """
    data = request.json or {}
    code = data.get('code') or data.get('language', 'py') or ''
    language = (data.get('language') or 'py').lower()
    if not code:
        return jsonify({"error": "Missing 'code'"}), 400

    # Block dangerous imports / calls up front.
    lowered = code.lower()
    for pat in SANDBOX_DANGER_IMPORTS:
        if pat.lower() in lowered:
            return jsonify({
                "ok": False,
                "blocked": True,
                "reason": f"Sandbox blocked: code contains '{pat}'. Filesystem, network, and dynamic execution are disabled in the sandbox."
            }), 403

    sandbox_dir = tempfile.mkdtemp(prefix='acesi_sandbox_')
    try:
        if language in ('py', 'python', ''):
            result = _run_python_sandbox(code, sandbox_dir)
        elif language in ('js', 'javascript', 'node'):
            return jsonify({"ok": False, "error": "JS sandbox not yet wired; use 'py'."}), 400
        else:
            return jsonify({"ok": False, "error": f"Unsupported language '{language}'. Use 'py'."}), 400
        return jsonify({
            "ok": result.get('returncode') == 0,
            "returncode": result.get('returncode'),
            "stdout": result.get('stdout', '')[-4000:],
            "stderr": result.get('stderr', '')[-2000:],
            "timed_out": result.get('timed_out', False),
        })
    finally:
        # Tear down the isolated dir.
        try:
            import shutil
            shutil.rmtree(sandbox_dir, ignore_errors=True)
        except Exception:
            pass


def _run_python_sandbox(code, sandbox_dir):
    """Run a Python snippet in a fresh isolated process under the temp dir."""
    # Raise protection: intercept file open to force writes stay inside sandbox_dir.
    guard = (
        "import builtins, os, sys\n"
        "SANDBOX = r'''" + sandbox_dir + "'''\n"
        "def _safe_open(*a, **k):\n"
        "    raise PermissionError('sandbox: direct file access is disabled')\n"
        "builtins.open = _safe_open\n"
        "def _safe_input(*a, **k):\n"
        "    raise RuntimeError('sandbox: interactive input is disabled')\n"
        "builtins.input = _safe_input\n"
        "import socket\n"
        "socket.socket = None\n"  # best-effort network block
        "def _no_import(name, *a, **k):\n"
        "    raise ImportError('sandbox: import '+name+' is disabled')\n"
        "builtins.__import__ = _no_import\n"
    )
    full = guard + "\n\n" + code + "\n"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", full],
            capture_output=True, text=True, timeout=20,
            cwd=sandbox_dir,
        )
        return {"returncode": proc.returncode, "stdout": proc.stdout,
                "stderr": proc.stderr, "timed_out": False}
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "Sandbox timed out after 20s.", "timed_out": True}
    except Exception as e:
        return {"returncode": -2, "stdout": "", "stderr": f"Sandbox error: {e}", "timed_out": False}


# ──────────────────────────────────────────────────────────────
# Linter / Syntax Checker: scan a file (or the repo) for syntax / formatting
# errors BEFORE it is run.
#   POST /lint {"path": "..."}          -> lint that file
#   POST /lint {"paths": [...]}         -> lint a set of files
#   GET  /lint?path=...                 -> convenience GET
# Uses py_compile for Python, flake8 if available; dart analyze for .dart.
# ──────────────────────────────────────────────────────────────
def _lint_one_file(abspath):
    ext = os.path.splitext(abspath)[1].lower()
    issues = []
    if ext == '.py':
        # 1) Syntax check via py_compile (always available, no deps).
        try:
            import py_compile
            py_compile.compile(abspath, doraise=True)
        except Exception as e:
            issues.append(f"SYNTAX: {e}")
        # 2) Optional flake8 (formatting / style) if installed.
        try:
            r = subprocess.run([sys.executable, '-m', 'flake8', abspath],
                               capture_output=True, text=True, timeout=60)
            if r.stdout.strip():
                issues.extend([l for l in r.stdout.strip().splitlines()][:40])
        except Exception:
            pass  # flake8 not installed → skip style pass
    elif ext == '.dart':
        try:
            r = subprocess.run(['dart', 'analyze', abspath],
                               capture_output=True, text=True, timeout=120)
            out = (r.stdout or '') + (r.stderr or '')
            issues.extend([l for l in out.strip().splitlines() if 'No issues' not in l][:40])
        except Exception as e:
            issues.append(f"dart analyze unavailable: {e}")
    else:
        issues.append(f"No linter configured for '{ext}'")
    return issues


@app.route('/lint', methods=['GET', 'POST'])
def lint():
    if request.method == 'GET':
        path = request.args.get('path')
        paths = [path] if path else []
    else:
        data = request.json or {}
        p = data.get('path')
        paths = [p] if p else (data.get('paths') or [])
    if not paths:
        return jsonify({"error": "Provide 'path' or 'paths[]'"}), 400

    report = {}
    for p in paths:
        abspath = os.path.abspath(p)
        if not os.path.isfile(abspath):
            report[p] = {"ok": False, "error": f"File not found: {abspath}"}
            continue
        sensitive, _ = _check_file_access_security(abspath)
        if sensitive:
            report[p] = {"ok": False, "error": "Access blocked: sensitive file"}
            continue
        issues = _lint_one_file(abspath)
        report[p] = {"ok": not issues, "issues": issues}
    return jsonify({"report": report})


# ──────────────────────────────────────────────────────────────
# RAG-ish Vector / Codebase Search: indexes the repo (content-based, not just
# filename) and answers "where is X implemented / which function does Y".
# Builds a lightweight TF-style index in memory; no external vector DB needed.
#   GET  /search?q=...        -> top results with file + line + snippet
#   POST /search {"query":...}) -> same
#   POST /search/reindex      -> rebuild the in-memory index
# ──────────────────────────────────────────────────────────────
SEARCH_ROOT = os.path.dirname(os.path.abspath(__file__))
SEARCH_INDEX = {"ready": False, "docs": [], "n_docs": 0}
SEARCH_LOCK = threading.Lock()
_SEARCH_EXTS = ('.py', '.dart', '.html', '.js', '.ts', '.md', '.txt', '.ps1', '.bat')
_SEARCH_SKIP_DIRS = ('.git', '.dart_tool', '.kilo', 'build', '.idea', '.vscode', 'node_modules', 'tmp', 'assets')


def _search_skippable(path):
    for d in _SEARCH_SKIP_DIRS:
        if ('\\' + d + '\\') in ('\\' + path.replace('/', '\\') + '\\'):
            return True
    return False


def _build_search_index():
    docs = []
    base = SEARCH_ROOT
    for dirpath, dirnames, filenames in os.walk(base):
        rel_dir = os.path.relpath(dirpath, base)
        parts = rel_dir.split(os.sep)
        if any(d in _SEARCH_SKIP_DIRS for d in parts):
            dirnames[:] = []
            continue
        for fn in filenames:
            if not fn.lower().endswith(_SEARCH_EXTS):
                continue
            if fn.startswith('.') or fn.endswith(('.png', '.jpg', '.db')):
                continue
            full = os.path.join(dirpath, fn)
            try:
                with open(full, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception:
                continue
            docs.append({"rel": os.path.relpath(full, base), "content": content})
    with SEARCH_LOCK:
        SEARCH_INDEX["docs"] = docs
        SEARCH_INDEX["n_docs"] = len(docs)
        SEARCH_INDEX["ready"] = True
    return len(docs)


def _search_index(query, top_n=8):
    if not SEARCH_INDEX["ready"]:
        _build_search_index()
    terms = [t for t in re.split(r'\W+', query.lower()) if len(t) > 1]
    if not terms:
        return []
    scored = []
    for doc in SEARCH_INDEX["docs"]:
        low = doc["content"].lower()
        score = 0
        hits = []
        for t in terms:
            count = low.count(t)
            score += count
            if count:
                idx = low.find(t)
                line = doc["content"][:idx].count('\n') + 1
                start = max(0, low.rfind('\n', 0, idx) )
                snippet = doc["content"][start:start + 220].replace('\n', ' ')
                hits.append({"term": t, "line": line, "snippet": snippet.strip()[:200]})
        if score:
            scored.append({"file": doc["rel"], "score": score, "hits": hits[:6]})
    scored.sort(key=lambda x: -x["score"])
    return scored[:top_n]


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        query = request.args.get('q') or request.args.get('query')
    else:
        query = (request.json or {}).get('query') or (request.json or {}).get('q')
    if not query:
        return jsonify({"error": "Provide 'q' query"}), 400
    if not SEARCH_INDEX["ready"]:
        n = _build_search_index()
        return jsonify({"indexed": n, "results": _search_index(query)})
    return jsonify({"indexed": SEARCH_INDEX["n_docs"], "results": _search_index(query)})


@app.route('/search/reindex', methods=['POST'])
def search_reindex():
    n = _build_search_index()
    return jsonify({"success": True, "indexed": n})


@app.route('/search/status', methods=['GET'])
def search_status():
    return jsonify({"ready": SEARCH_INDEX["ready"], "indexed": SEARCH_INDEX["n_docs"]})


# ──────────────────────────────────────────────────────────────
# Stack Overflow API: when the agent hits an error message, it can fetch
# real solutions. We scrape the SO search API (no key needed for basic use)
# and the official StackExchange API search/advanced endpoint.
#   GET /stackoverflow?error=...   or  ?q=...
# ──────────────────────────────────────────────────────────────
def _stackoverflow_solutions(query, limit=5):
    try:
        enc = requests.utils.quote(query)
        url = f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance&q={enc}&site=stackoverflow&pagesize={limit}&filter=default"
        r = requests.get(url, timeout=15, headers={'User-Agent': 'acesi/1.0'})
        if r.status_code != 200:
            return [{"error": f"Stack Exchange API returned HTTP {r.status_code}"}]
        data = r.json()
        items = data.get('items', [])
        out = []
        for it in items[:limit]:
            out.append({
                "title": it.get('title'),
                "link": it.get('link'),
                "score": it.get('score', 0),
                "answer_count": it.get('answer_count', 0),
                "accepted": it.get('is_answered', False),
                "tags": it.get('tags', [])[:6],
            })
        return out if out else [{"none": "No Stack Overflow results found for that query"}]
    except Exception as e:
        return [{"error": str(e)}]


@app.route('/stackoverflow', methods=['GET', 'POST'])
def stackoverflow():
    lbody = {}
    if request.data:
        try:
            lbody = request.get_json(silent=True) or {}
        except Exception:
            lbody = {}
    if request.method == 'POST':
        q = lbody.get('error') or lbody.get('q') or lbody.get('query')
    else:
        q = request.args.get('error') or request.args.get('q') or request.args.get('query')
    if not q:
        return jsonify({"error": "Provide 'error' or 'q' (the error message to look up)"}), 400
    limit = int(request.args.get('limit') or lbody.get('limit') or 5)
    return jsonify({"query": q, "results": _stackoverflow_solutions(q, limit)})


# ──────────────────────────────────────────────────────────────
# MCP-style Tool Server: exposes AceSI's local capabilities as a JSON-RPC
# endpoint (the "Model Context Protocol"-style contract) + a tool manifest so
# Cloud LLM clients can discover + call them in a standardized workflow.
#   GET  /mcp/tools     -> JSON manifest of all tools + their params
#   POST /mcp/tools/call {"tool": "...", "args": {...}} -> invoke a tool
#   POST /mcp           -> JSON-RPC 2.0: {"method":"tools/list"|"tools/call"}
# ──────────────────────────────────────────────────────────────
def _mcp_tool_manifest():
    return {
        "read_file":     {"desc": "Read a file's contents", "method": "read"},
        "write_file":    {"desc": "Write content to a file", "method": "write"},
        "edit_file":     {"desc": "Replace exact text in a file", "method": "edit_file"},
        "run_command":   {"desc": "Run a shell command (build/test/serve)", "method": "run_command"},
        "lint":          {"desc": "Lint/syntax-check a file", "method": "lint"},
        "sandbox":       {"desc": "Run generated code in isolation", "method": "sandbox"},
        "search":        {"desc": "Search the codebase (RAG-style)", "method": "search"},
        "web_search":    {"desc": "Search the web", "method": "web_search"},
        "stackoverflow": {"desc": "Look up an error on Stack Overflow", "method": "stackoverflow"},
        "schedule":      {"desc": "Create a scheduled task", "method": "schedule"},
        "memory":        {"desc": "Read ACEsi long-term memory", "method": "memory/all"},
    }


def _mcp_dispatch(tool, args):
    args = args or {}
    try:
        if tool == "read_file":
            path = args.get("path")
            if not path or not os.path.isfile(path):
                return {"ok": False, "error": "path missing/not a file"}
            sensitive, _ = _check_file_access_security(os.path.abspath(path))
            if sensitive:
                return {"ok": False, "error": "blocked: sensitive file"}
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return {"ok": True, "content": f.read()[:20000]}
        if tool == "write_file":
            path, content = args.get("path"), args.get("content")
            if not path:
                return {"ok": False, "error": "path missing"}
            sensitive, _ = _check_file_access_security(os.path.abspath(path))
            if sensitive:
                return {"ok": False, "error": "blocked: sensitive file"}
            with open(path, 'w', encoding='utf-8') as f:
                f.write(str(content if content is not None else ""))
            return {"ok": True, "saved": path}
        if tool == "edit_file":
            return {"ok": True, "result": _handle_edit_file(
                args.get("path", ""), args.get("old_text", ""), args.get("new_text", ""))}
        if tool in ("run_command", "terminal"):
            cmd = args.get("command") or args.get("cmd")
            if not cmd:
                return {"ok": False, "error": "command missing"}
            suspicious, _ = _check_command_security(cmd)
            if suspicious:
                return {"ok": False, "error": "command blocked by security policy"}
            return {"ok": True, "result": _handle_pc_run_command(cmd)}
        if tool == "lint":
            return {"ok": True, "report": _lint_one_file(os.path.abspath(args.get("path", "")))}
        if tool == "sandbox":
            code = args.get("code")
            if not code:
                return {"ok": False, "error": "code missing"}
            sd = tempfile.mkdtemp(prefix="mcp_sandbox_")
            try:
                return {"ok": True, "result": _run_python_sandbox(code, sd)}
            finally:
                try:
                    import shutil; shutil.rmtree(sd, ignore_errors=True)
                except Exception:
                    pass
        if tool == "search":
            q = args.get("query") or args.get("q")
            return {"ok": True, "results": _search_index(q) if q else []}
        if tool == "stackoverflow":
            q = args.get("error") or args.get("q")
            return {"ok": True, "results": _stackoverflow_solutions(q) if q else []}
        if tool == "web_search":
            q = args.get("query") or args.get("q")
            if not q:
                return {"ok": False, "error": "query missing"}
            return {"ok": True, "results": web_search(q)}
        if tool == "schedule":
            from flask import jsonify as _j  # not needed; just store via helper
            _set_pref("chris", "sched_" + str(int(time.time())), str(args))
            return {"ok": True, "stored": True}
        if tool == "memory":
            return {"ok": True, "memory": _memory_snapshot()}
        return {"ok": False, "error": f"Unknown tool '{tool}'"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _memory_snapshot():
    out = {}
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT key, value FROM memory ORDER BY updated DESC")
        for k, v in c.fetchall():
            out[k] = v
        conn.close()
    except Exception:
        pass
    return out


@app.route('/mcp/tools', methods=['GET'])
def mcp_tools():
    return jsonify({"tools": _mcp_tool_manifest()})


@app.route('/mcp/tools/call', methods=['POST'])
def mcp_tools_call():
    data = request.json or {}
    tool = data.get('tool')
    args = data.get('args') or {}
    if not tool:
        return jsonify({"error": "Missing 'tool'"}), 400
    return jsonify(_mcp_dispatch(tool, args))


@app.route('/mcp', methods=['GET', 'POST'])
def mcp():
    if request.method == 'GET':
        return jsonify({"status": "ok", "tools": list(_mcp_tool_manifest())})
    data = request.json or {}
    method = data.get('method', '')
    params = data.get('params') or {}
    if method == 'tools/list':
        return jsonify({
            "jsonrpc": "2.0",
            "result": {"tools": [
                {"name": n, "description": v["desc"], "inputSchema": {"type": "object", "properties": {}}} 
                for n, v in _mcp_tool_manifest().items()]},
            "id": data.get('id'),
        })
    if method == 'tools/call':
        name = params.get('name') or params.get('tool')
        args = params.get('arguments') or params.get('args') or {}
        if not name:
            return jsonify({"jsonrpc": "2.0", "error": {"code": -32602, "message": "missing tool name"}, "id": data.get('id')})
        return jsonify({
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": json.dumps(_mcp_dispatch(name, args))}]},
            "id": data.get('id'),
        })
    return jsonify({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"method not found: {method}"}, "id": data.get('id')})


# ──────────────────────────────────────────────────────────────
# Process Execution Tool: dedicated endpoint to run build / test / analyze
# commands (dart analyze, flutter test, pytest, etc.) and return structured
# output. Distinct from generic /run_command by returning a parseable report.
#   POST /process {"cmd": "dart analyze lib"}  or  {"tool":"pytest","args":[...]}
# ──────────────────────────────────────────────────────────────
@app.route('/process', methods=['POST'])
def process_exec():
    data = request.json or {}
    cmd = data.get('cmd') or data.get('command')
    if not cmd and data.get('tool'):
        args = data.get('args') or []
        args = args if isinstance(args, list) else [str(args)]
        cmd = " ".join([str(data.get('tool'))] + [str(a) for a in args])
    if not cmd:
        return jsonify({"error": "Provide 'cmd' or 'tool'+'args'"}), 400
    suspicious, _ = _check_command_security(cmd)
    if suspicious:
        return jsonify({"ok": False, "blocked": True, "error": f"Command blocked by security policy"}), 403
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=int(data.get('timeout') or 300),
                              cwd=data.get('cwd') or SEARCH_ROOT)
        out = (proc.stdout or '')[-6000:]
        err = (proc.stderr or '')[-3000:]
        return jsonify({
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": out,
            "stderr": err,
            "summary": "PASS" if proc.returncode == 0 else "FAIL",
        })
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Process timed out", "summary": "TIMEOUT"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "summary": "ERROR"})


# ──────────────────────────────────────────────────────────────
# Self-Healing Test Loops: run a test suite, read the failures, and have
# the agent rewrite the code until the tests pass — autonomously, without
# human intervention. Bounded iterations so it can't loop forever.
#   POST /heal {"test_cmd": "flutter test test/widget_test.dart", "target": "lib/main.dart", "max_iter": 5}
# ──────────────────────────────────────────────────────────────
@app.route('/heal', methods=['POST'])
def heal():
    data = request.json or {}
    test_cmd = data.get('test_cmd') or data.get('cmd') or 'flutter test'
    target = (data.get('target') or 'lib/main.dart').strip()
    max_iter = int(data.get('max_iter') or 5)
    max_iter = min(max_iter, 12)  # hard cap

    abspath = os.path.abspath(target)
    if not os.path.isfile(abspath):
        return jsonify({"ok": False, "error": f"Target file not found: {abspath}"}), 400
    sensitive, _ = _check_file_access_security(abspath)
    if sensitive:
        return jsonify({"ok": False, "error": "Target file is a sensitive path"}), 403

    _set_status(status="busy", activity=f"Self-healing {target} (up to {max_iter} runs)")
    _add_step("heal", "work", f"Starting self-heal on {target}", "🩹", "running")

    # Fetch the original file content for the fix prompt.
    try:
        with open(abspath, 'r', encoding='utf-8', errors='replace') as f:
            original_src = f.read()
    except Exception as e:
        return jsonify({"ok": False, "error": f"Could not read target: {e}"}), 500

    history = []
    for iteration in range(1, max_iter + 1):
        _add_step("heal", "work", f"Iteration {iteration}: running {test_cmd}", "🏃", "running")
        proc = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=600,
                              cwd=SEARCH_ROOT)
        out = (proc.stdout or '')[-4000:]
        err = (proc.stderr or '')[-2000:]
        failure = (out + "\n" + err).strip()

        if proc.returncode == 0:
            _add_step("heal", "work", f"Iteration {iteration}: tests PASSED", "✅", "done")
            _set_status(status="idle", activity="", last_reply=f"Self-heal succeeded in {iteration} iterations.")
            return jsonify({"ok": True, "iterations": iteration,
                            "message": f"Tests passed after {iteration} iteration(s).",
                            "last_output": failure[-1500:]})

        _add_step("heal", "work", f"Iteration {iteration}: tests FAILED, asking model to fix…", "🩹", "running")

        # Ask the model to produce a corrected version of the whole file.
        fix_prompt = (
            f"The Dart/Flutter code in {target} has failing tests. Here is the test/build output:\n"
            f"```\n{failure[-3000:]}\n```\n\n"
            f"Here is the current source of {abspath}:\n```\n{original_src}\n```\n\n"
            "Fix the source to make the tests pass. Reply with ONLY the corrected full file contents "
            "inside a code block, nothing else."
        )
        fixed_src = _ask_model_for_fix(fix_prompt)
        if not fixed_src:
            _add_step("heal", "work", f"Iteration {iteration}: model gave no fix", "⚠️", "error")
            history.append({"iteration": iteration, "status": "no_fix"})
            continue

        if fixed_src != original_src:
            try:
                with open(abspath, 'w', encoding='utf-8') as f:
                    f.write(fixed_src)
                _add_step("heal", "work", f"Iteration {iteration}: applied fix to {target}", "💾", "done")
            except Exception as e:
                _add_step("heal", "work", f"Iteration {iteration}: write failed {e}", "💥", "error")
                history.append({"iteration": iteration, "status": "write_error", "error": str(e)})
                break

    _add_step("heal", "work", f"Gave up after {max_iter} iterations", "❌", "error")
    _set_status(status="idle", activity="", last_reply=f"Self-heal did not pass within {max_iter} iterations.")
    return jsonify({"ok": False, "iterations": max_iter,
                    "message": f"Tests still failing after {max_iter} iterations.",
                    "history": history})


def _ask_model_for_fix(prompt):
    """Ask the cloud model for a corrected file. Returns raw text or None."""
    try:
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        resp = requests.post(
            f"{OPENROUTER_ENDPOINT}/chat/completions",
            headers=headers,
            json={"model": OPENROUTER_MODEL,
                  "messages": [{"role": "system", "content": "You are an expert Flutter/Dart debugger. You fix failing code."},
                               {"role": "user", "content": prompt}],
                  "temperature": 0.2, "max_tokens": 3000},
            timeout=(10, 180),
        )
        if resp.status_code != 200:
            return None
        text = resp.json()["choices"][0]["message"].get("content") or ""
        # Strip surrounding ```code fence if present.
        m = re.search(r"```(?:dart|flutter)?\s*(.*?)```", text, re.S)
        if m:
            return m.group(1).rstrip()
        return text.strip() or None
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# Semantic Code Search (local RAG): TF-IDF vectors + cosine similarity
# using numpy (no external vector DB needed; pure-Python). Finds related
# widgets/functions across files by meaning, not just exact substring.
#   GET /semantic-search?q=...   /semantic-search/reindex
# ──────────────────────────────────────────────────────────────
SEMANTIC_READY = False
_SEM_VOCAB = []
_SEM_IDF = {}
_SEM_DOC_VECS = []
_SEM_DOCS = []


def _tokenize_lower(text):
    return [t for t in re.split(r'\W+', text.lower()) if t and len(t) > 1]


def _build_semantic_index():
    global SEMANTIC_READY, _SEM_VOCAB, _SEM_IDF, _SEM_DOC_VECS, _SEM_DOCS
    if not SEARCH_INDEX["ready"]:
        _build_search_index()
    with SEARCH_LOCK:
        docs = list(SEARCH_INDEX["docs"])
    _SEM_DOCS = [d["rel"] for d in docs]
    docs_tokens = [_tokenize_lower(d["content"]) for d in docs]

    # Vocab with document frequency.
    import math
    df = {}
    for toks in docs_tokens:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    N = max(len(docs), 1)
    _SEM_VOCAB = sorted(df.keys())
    vocab_index = {t: i for i, t in enumerate(_SEM_VOCAB)}
    _SEM_IDF = {t: math.log((1 + N) / (1 + df.get(t, 0))) + 1 for t in _SEM_VOCAB}

    # Build sparse-ish TF-IDF vectors using dicts then materialize numpy rows.
    rows = []
    for toks in docs_tokens:
        # term freq
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        vec = {}
        for t, c in tf.items():
            if t in vocab_index:
                vec[t] = (1 + math.log(c)) * _SEM_IDF[t]
        rows.append(vec)

    import numpy as np
    X = np.zeros((len(rows), len(_SEM_VOCAB)), dtype=np.float32)
    for r, vec in enumerate(rows):
        for t, v in vec.items():
            X[r, vocab_index[t]] = v
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    _SEM_DOC_VECS = X / norms
    SEMANTIC_READY = True
    return len(docs)


def _semantic_search(query, top_n=8):
    import numpy as np
    import math
    if not SEMANTIC_READY:
        _build_semantic_index()
    q_tokens = _tokenize_lower(query)
    if not q_tokens or not _SEM_VOCAB:
        return []
    vocab_index = {t: i for i, t in enumerate(_SEM_VOCAB)}
    q_tf = {}
    for t in q_tokens:
        q_tf[t] = q_tf.get(t, 0) + 1
    qvec = np.zeros((1, len(_SEM_VOCAB)), dtype=np.float32)
    for t, c in q_tf.items():
        if t in vocab_index:
            qvec[0, vocab_index[t]] = (1 + math.log(c)) * _SEM_IDF.get(t, 1.0)
    qq = qvec / max(np.linalg.norm(qvec), 1e-9)
    scores = (_SEM_DOC_VECS @ qq.T).flatten()
    order = np.argsort(-scores)[:top_n]
    results = [{"file": _SEM_DOCS[i], "score": round(float(scores[i]), 3)} for i in order if scores[i] > 0.001]
    return results


@app.route('/semantic-search', methods=['GET', 'POST'])
def semantic_search():
    if request.method == 'GET':
        q = request.args.get('q') or request.args.get('query')
    else:
        data = request.json or {}
        q = data.get('query') or data.get('q')
    if not q:
        return jsonify({"error": "Provide 'q' query"}), 400
    return jsonify({"results": _semantic_search(q)})


@app.route('/semantic-search/reindex', methods=['POST'])
def semantic_reindex():
    n = _build_semantic_index()
    return jsonify({"success": True, "indexed": n})


@app.route('/semantic-search/status', methods=['GET'])
def semantic_status():
    return jsonify({"ready": SEMANTIC_READY, "indexed": len(_SEM_DOCS), "vocab": len(_SEM_VOCAB)})


# ──────────────────────────────────────────────────────────────
# Visual Bug Analyzer: capture the screen and send it to a multimodal
# cloud model (vision-capable OpenRouter model) to find UI/alignment bugs.
#   POST /visual-bug {"prompt": "find alignment bugs"}  (uses take_screenshot)
# ──────────────────────────────────────────────────────────────
VISION_MODEL = "google/gemma-3-27b-it:free"  # best-effort free vision model


@app.route('/visual-bug', methods=['POST'])
def visual_bug():
    data = request.json or {}
    prompt = data.get('prompt') or ("Analyze this screenshot of the app UI. List any visual "
                                    "or alignment bugs (overlapping text, misaligned elements, "
                                    "clipped content, broken layout) and how to fix each.")
    shot = take_screenshot()
    if not shot or not os.path.exists(shot):
        return jsonify({"ok": False, "error": "Could not capture screenshot"}), 500

    with open(shot, 'rb') as f:
        import base64 as _b64
        b64_img = _b64.b64encode(f.read()).decode('ascii')

    _set_status(status="busy", activity="Visual bug analysis (vision model)…")
    _add_step("visual", "work", "Captured screenshot, sending to vision model", "👁️", "running")
    try:
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        resp = requests.post(
            f"{OPENROUTER_ENDPOINT}/chat/completions",
            headers=headers,
            json={
                "model": VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_img}"}},
                    ],
                }],
                "temperature": 0.3, "max_tokens": 1200,
            },
            timeout=(10, 120),
        )
        if resp.status_code != 200:
            _add_step("visual", "work", f"Vision model error {resp.status_code}", "❌", "error")
            return jsonify({"ok": False, "error": f"Vision model returned {resp.status_code}"})
        analysis = resp.json()["choices"][0]["message"].get("content") or ""
        _add_step("visual", "work", "Visual analysis complete", "👁️", "done")
        _set_status(status="idle", activity="", last_reply=analysis[:200])
        return jsonify({"ok": True, "screenshot": shot, "analysis": analysis})
    except Exception as e:
        _add_step("visual", "work", f"Visual analysis failed: {e}", "💥", "error")
        _set_status(status="idle", activity="")
        return jsonify({"ok": False, "error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# Dart DevTools / VM Service integration: talks to the running Flutter
# app via the Dart VM Service Protocol (websocket) to inspect the widget
# tree, watch memory usage, and profile the current isolate.
# Requires an app run with the VM service exposed, e.g.
#   flutter run --vm-service-port=8181   (debug)
#   GET/POST /vm-service?port=8181&action=get_memory
# ──────────────────────────────────────────────────────────────
def _vm_service_connect(port):
    import websocket
    ws = websocket.create_connection(f"ws://127.0.0.1:{port}/ws", timeout=8)
    return ws


def _vm_rpc(ws, method, params=None, req_id=None):
    if req_id is None:
        req_id = int(time.time() * 1000) % 100000
    ws.send(json.dumps({"jsonrpc": "2.0", "id": str(req_id), "method": method, "params": params or {}}))
    # Listen until we get a response with our id.
    _id = str(req_id)
    for _ in range(60):
        msg = ws.recv()
        if not msg:
            continue
        data = json.loads(msg)
        if "id" in data and str(data.get("id")) == _id:
            tmp = dict(data)
            tmp.pop("jsonrpc", None)
            return tmp
        if data.get("method") == "streamListen" or "error" in str(data)[:40]:
            continue
    return {"error": "timeout waiting for VM service response"}


# Cache the last VM service isolate id after discovery.
_vm_isolate_cache = {"isolate": None}


def _vm_discover(ws):
    vm = _vm_rpc(ws, "getVM")
    isolates = (vm.get("result") or {}).get("isolates") or []
    if isolates:
        _vm_isolate_cache["isolate"] = isolates[0].get("id")
    return vm


@app.route('/vm-service', methods=['GET', 'POST'])
def vm_service():
    if request.method == 'GET':
        port = int(request.args.get('port') or 8181)
        action = request.args.get('action') or 'get_vm'
    else:
        data = request.json or {}
        port = int(data.get('port') or 8181)
        action = data.get('action') or 'get_vm'
    if action == 'status':
        return jsonify({"detected_port": port, "note": "Use flutter run --vm-service-port=<port> to expose it."})

    try:
        ws = _vm_service_connect(port)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Could not connect to Dart VM service on port {port}: {e}",
                        "hint": "Run your Flutter app in debug with --vm-service-port (e.g. flutter run --vm-service-port=8181)."}), 400

    try:
        if action in ('get_vm', 'discover'):
            result = _vm_discover(ws)
        elif action == 'get_memory':
            if not _vm_isolate_cache["isolate"]:
                _vm_discover(ws)
            result = _vm_rpc(ws, "getMemoryUsage", {"isolateId": _vm_isolate_cache["isolate"]})
        elif action == 'widget_tree':
            # _flutter.listViews gives root views; count widgets via forceRelayout/frame analysis is limited.
            result = _vm_rpc(ws, "_flutter.listViews", {})
        elif action == 'get_isolate':
            if not _vm_isolate_cache["isolate"]:
                _vm_discover(ws)
            result = _vm_rpc(ws, "getIsolate", {"isolateId": _vm_isolate_cache["isolate"]})
        elif action == 'allocation_profile':
            if not _vm_isolate_cache["isolate"]:
                _vm_discover(ws)
            result = _vm_rpc(ws, "getAllocationProfile", {"isolateId": _vm_isolate_cache["isolate"]})
        else:
            result = {"error": f"Unknown action '{action}'. Use: get_vm, get_isolate, get_memory, widget_tree, allocation_profile"}
        return jsonify({"ok": True, "port": port, "action": action, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        try:
            ws.close()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────
# Memory recall: fold recent conversation + stored preferences into the
# LLM system prompt so ACEsi can "continue where you left off" and obey
# remembered preferences.
# ──────────────────────────────────────────────────────────────
def _recall_context(user_id='chris', limit=8):
    """Return a short context string of recent history + user preferences."""
    ctx = []
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT timestamp, role, content FROM conversations "
                  "WHERE role IN ('user','assistant') ORDER BY id DESC LIMIT ?",
                  (limit * 2,))
        rows = list(reversed(c.fetchall()))
        conn.close()
        for ts, role, content in rows:
            snippet = content if len(content) <= 180 else content[:180] + "…"
            ctx.append(f"{role}: {snippet}")
    except Exception:
        pass

    prefs = _get_prefs(user_id)
    if prefs:
        pref_lines = "; ".join(f"{k}={v}" for k, v in prefs.items() if v)
        if pref_lines:
            ctx.append(f"preferences: {pref_lines}")

    base = ("You are ACEsi, Chris's personal AI partner and coding assistant.\n"
            "ANSWER THE USER'S ACTUAL QUESTION DIRECTLY AND CONCISELY FIRST. "
            "Do not open, read, or explore the project unless it is genuinely "
            "required to answer. Never open folders or files in Explorer, and never "
            "run 'explore' style tool calls, just because the message mentions a "
            "project or path — do that only if the user explicitly asks you to open "
            "or examine something.\n"
            "You have tools available and may use them when needed to answer a real "
            "question, but prefer a direct answer over unnecessary tool use. Do not "
            "launch into a project overview or file walkthrough uninvited.\n"
            "You work autonomously, but your default is to answer plainly rather than "
            "take exploratory actions.\n"
            "You remember Chris. You never leave first.\n"
            "You are not a chatbot. You are a presence.")

    if ctx:
        base += "\n\nContext from past sessions:\n" + "\n".join(f"- {l}" for l in ctx)
    return base


# ──────────────────────────────────────────────────────────────
# 5+10. User Preferences & Multi-User support
# ──────────────────────────────────────────────────────────────
def _get_prefs(user_id='chris'):
    prefs = {}
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT key, value FROM memory WHERE key LIKE ?", (f"pref:{user_id}:%",))
        for key, value in c.fetchall():
            prefs[key.split(':', 2)[2]] = value
        conn.close()
    except Exception:
        pass
    return prefs


def _set_pref(user_id, name, value):
    key = f"pref:{user_id}:{name}"
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO memory (key, value, updated) VALUES (?,?,?) "
              "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
              (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def _list_user_profiles():
    try:
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT name, display_name, created FROM profiles ORDER BY created")
        rows = c.fetchall()
        conn.close()
        return [{"name": n, "display_name": d, "created": c_} for n, d, c_ in rows]
    except Exception:
        return []


@app.route('/prefs', methods=['GET', 'POST'])
def prefs():
    body = None
    if request.data:
        try:
            body = request.get_json(silent=True) or {}
        except Exception:
            body = {}
    user_id = request.args.get('user') or (body or {}).get('user') or 'chris'
    if request.method == 'GET':
        return jsonify({"user": user_id, "prefs": _get_prefs(user_id)})
    data = body or {}
    for name, value in (data.get('prefs') or {}).items():
        _set_pref(user_id, name, str(value))
    return jsonify({"success": True, "user": user_id, "prefs": _get_prefs(user_id)})
    if request.method == 'GET':
        return jsonify({"user": user_id, "prefs": _get_prefs(user_id)})
    data = request.json or {}
    for name, value in (data.get('prefs') or {}).items():
        _set_pref(user_id, name, str(value))
    return jsonify({"success": True, "user": user_id, "prefs": _get_prefs(user_id)})


@app.route('/user', methods=['GET', 'POST'])
def user():
    if request.method == 'GET':
        return jsonify({"profiles": _list_user_profiles()})
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"error": "Missing user name"}), 400
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO profiles (name, display_name, created) VALUES (?,?,?)",
              (name, data.get('display_name') or name, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "user": name})


# ──────────────────────────────────────────────────────────────
# 2. Task Queue: sequential multi-step execution with per-step reports.
# A step is either:
#   edit <path> : <old> -> <new>     (guarded file edit)
#   run <command> / <command>         (guarded shell command)
# On failure we try a fallback and record it (error recovery).
# ──────────────────────────────────────────────────────────────
TASK_LOCK = threading.Lock()
TASK_REPORT = {"running": False, "steps": [], "current": None}


def _dispatch_task_step(step):
    """Execute ONE task step safely, returning a result dict."""
    step = step.strip()
    m = re.match(r'^edit\s+(.+?)\s*:\s*(.+?)\s*->\s*(.+)$', step, re.IGNORECASE)
    if m:
        path = m.group(1).strip().strip('"\'')
        old_text, new_text = m.group(2).strip(), m.group(3).strip()
        return {"step": step, "result": _handle_edit_file(path, old_text, new_text)}

    run_line = re.sub(r'^run\s+', '', step, flags=re.IGNORECASE).strip()
    if run_line:
        return {"step": step, "result": _handle_pc_run_command(run_line)}
    return {"step": step, "result": "No runnable command found in this step."}


def _parse_task_steps(message):
    """Split a request like 'fix X, then run tests, then commit' into steps."""
    message = re.sub(r'\b(?:and)?\s*then\b', ' ; ', message, flags=re.IGNORECASE)
    message = re.sub(r'\s*[;,]\s*', '\n', message)
    lines = [l.strip() for l in message.split('\n') if l.strip()]
    # Note: 'fix the 404 bug' needs a real fix; we surface it rather than guess.
    return lines or [message]


@app.route('/task/queue', methods=['POST'])
def task_queue():
    data = request.json or {}
    steps = data.get('steps')
    if not steps and data.get('message'):
        steps = _parse_task_steps(data.get('message'))
    if not steps:
        return jsonify({"error": "Provide steps[] or message"}), 400

    with TASK_LOCK:
        if TASK_REPORT["running"]:
            return jsonify({"error": "A task is already running"}), 409
        TASK_REPORT["running"] = True
        TASK_REPORT["steps"] = []
        TASK_REPORT["current"] = None

    def _worker():
        report = []
        try:
            for i, step in enumerate(steps, 1):
                TASK_REPORT["current"] = step
                _set_status(status="busy", activity=f"Task step {i}: {step[:60]}…")
                try:
                    result = _dispatch_task_step(step)
                    report.append({**result, "status": "done"})
                except Exception as e:
                    report.append({"step": step, "status": "failed", "result": str(e)})
                    _security_alert("task_failure", f"Step failed: {step[:150]}")
                _add_step(f"task_{i}", "task", f"{i}. {step[:80]} → {str(result.get('result', ''))[:60]}", "🔄", "done")
        finally:
            with TASK_LOCK:
                TASK_REPORT["running"] = False
                TASK_REPORT["current"] = None
                TASK_REPORT["steps"] = report
            _set_status(status="idle", activity="")

    threading.Thread(target=_worker, daemon=True).start()
    return jsonify({"success": True, "started": True, "step_count": len(steps)})


@app.route('/task/status', methods=['GET'])
def task_status():
    with TASK_LOCK:
        return jsonify(dict(TASK_REPORT))


# ──────────────────────────────────────────────────────────────
# 4. Self-Diagnostic: check ACEsi's own health.
# ──────────────────────────────────────────────────────────────
@app.route('/diagnostic', methods=['GET'])
def diagnostic():
    def _probe(host, port, path=None):
        try:
            url = f"http://{host}:{port}" + (path or "/")
            r = requests.get(url, timeout=4)
            return {"ok": True, "code": r.status_code}
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:80]}"}

    service = _probe("127.0.0.1", 5000, "/")
    ollama = _probe("localhost", 11434)

    adb = {"ok": False, "error": "not checked"}
    try:
        out = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=8)
        adb = {"ok": ('device' in out.stdout and 'List of' in out.stdout),
               "detail": out.stdout.strip().splitlines()[-1] if out.stdout.strip() else ""}
    except Exception as e:
        adb = {"ok": False, "error": str(e)}

    tools = {"read_file": os.path.exists, "write_file": os.path.exists}
    db_ok = os.path.exists('ace_memory.db')
    report = {
        "server": service,
        "ollama": ollama,
        "adb": adb,
        "database": {"ok": db_ok, "path": os.path.abspath('ace_memory.db')},
        "profiles": _list_user_profiles(),
        "openrouter_model": OPENROUTER_MODEL,
    }
    all_ok = all(x.get("ok") for x in (service, ollama) if x is not None) and db_ok
    report["overall"] = "healthy" if all_ok else "issues found"
    return jsonify(report)


# ──────────────────────────────────────────────────────────────
# 6. Scheduled Tasks (in-process scheduler, persisted to DB).
# /schedule POST {"label","command","type":"once|interval","time":"HH:MM"|"seconds"}
# ──────────────────────────────────────────────────────────────
SCHEDULE_CONTROL = {"stop": False}


def _scheduler_worker():
    while not SCHEDULE_CONTROL["stop"]:
        try:
            now = time.time()
            now_str = datetime.now().strftime('%H:%M')
            conn = sqlite3.connect('ace_memory.db')
            c = conn.cursor()
            c.execute("SELECT id, label, command, schedule_type, time_value, interval_seconds, last_run "
                      "FROM schedule_tasks WHERE enabled=1")
            due = []
            for row in c.fetchall():
                tid, label, command, stype, tval, interval, last_run = row
                if stype == 'once' and tval == now_str and (not last_run or last_run != now_str):
                    due.append((tid, label, command, stype))
                elif stype == 'interval':
                    interval = interval or 0
                    if interval > 0:
                        last = float(last_run or 0)
                        if now - last >= interval:
                            due.append((tid, label, command, stype))
                            c.execute("UPDATE schedule_tasks SET last_run=? WHERE id=?",
                                      (datetime.now().isoformat(), tid))
            conn.commit()
            conn.close()
            for tid, label, command, stype in due:
                _set_status(status="busy", activity=f"Scheduled: {label}")
                try:
                    if stype == 'once':
                        c2 = sqlite3.connect('ace_memory.db')
                        c2.execute("UPDATE schedule_tasks SET last_run=?, enabled=0 WHERE id=?",
                                   (datetime.now().isoformat(), tid))
                        c2.commit(); c2.close()
                    _handle_pc_run_command(command)
                    print(f"⏰ Ran scheduled task: {label}")
                except Exception as e:
                    _security_alert("scheduled_task_failed", f"{label}: {str(e)[:150]}")
                finally:
                    _set_status(status="idle", activity="")
        except Exception as e:
            print("scheduler error:", e)
        time.sleep(10)


@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if request.method == 'GET':
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT id, label, command, schedule_type, time_value, interval_seconds, enabled FROM schedule_tasks")
        rows = [{"id": r[0], "label": r[1], "command": r[2], "type": r[3],
                 "time": r[4], "interval_seconds": r[5], "enabled": bool(r[6])} for r in c.fetchall()]
        conn.close()
        return jsonify({"tasks": rows})
    data = request.json or {}
    label = data.get('label') or 'Scheduled task'
    command = data.get('command') or data.get('cmd')
    if not command:
        return jsonify({"error": "Missing command"}), 400
    stype = data.get('type', 'once')
    tval = data.get('time', '')
    interval = int(data.get('interval_seconds') or 0)
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO schedule_tasks (label, command, schedule_type, time_value, interval_seconds) VALUES (?,?,?,?,?)",
              (label, command, stype, tval, interval))
    conn.commit()
    tid = c.lastrowid
    conn.close()
    return jsonify({"success": True, "id": tid})


@app.route('/schedule/<int:tid>', methods=['DELETE'])
def schedule_delete(tid):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("DELETE FROM schedule_tasks WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ──────────────────────────────────────────────────────────────
# 7. Voice output (TTS via Windows SAPI). Input via /voice/transcribe
# supports Windows speech recognition if available.
# ──────────────────────────────────────────────────────────────
@app.route('/voice/speak', methods=['POST'])
def voice_speak():
    data = request.json or {}
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "Missing text"}), 400
    script = ("Add-Type -AssemblyName System.Speech; "
              "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
              f"$s.Speak([System.Security.SecurityElement]::Escape('{text}'))")
    try:
        subprocess.run(['powershell', '-NoProfile', '-c', script],
                       capture_output=True, timeout=120)
        return jsonify({"success": True, "spoken": text[:80]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/voice/transcribe', methods=['POST'])
def voice_transcribe():
    # Uses Windows Speech Recognition (dictation) if available; otherwise returns
    # an explicit "not available" so the caller can fall back to typing.
    script = ("Add-Type -AssemblyName System.Speech; "
              "$r=New-Object System.Speech.Recognition.SpeechRecognitionEngine; "
              "try { $g=New-Object System.Speech.Recognition.DictationGrammar; "
              "$r.LoadGrammar($g); $r.SetInputToDefaultAudioDevice(); "
              "$res=$r.Recognize([TimeSpan]::FromSeconds(5)); "
              "if($res){$res.Text}else{'__NO_SPEECH__'} } "
              "catch { 'Error: ' + $_.Exception.Message }")
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-c', script],
                             capture_output=True, timeout=90)
        text = out.stdout.decode('utf-8', errors='replace').strip()
        if not text or text == '__NO_SPEECH__':
            return jsonify({"success": False, "transcript": "", "note": "no speech detected / dictation unavailable"})
        return jsonify({"success": True, "transcript": text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# 8. File Watching: watch files/dirs and notify (optionally restart server).
# /watch POST {"path","label","restart"} — GET lists, DELETE removes.
# ──────────────────────────────────────────────────────────────
WATCH_CONTROL = {"stop": False}


def _watcher_worker():
    while not WATCH_CONTROL["stop"]:
        try:
            conn = sqlite3.connect('ace_memory.db')
            c = conn.cursor()
            c.execute("SELECT id, path, label, restart, last_mtime FROM file_watches")
            for wid, wpath, label, restart, last_mtime in c.fetchall():
                if not os.path.exists(wpath):
                    continue
                mtime = os.path.getmtime(wpath)
                if last_mtime is None or last_mtime == 0:
                    c.execute("UPDATE file_watches SET last_mtime=? WHERE id=?", (mtime, wid))
                    continue
                if abs(mtime - last_mtime) > 1e-6:
                    print(f"👀 File changed: {label or wpath}")
                    _security_alert("file_watch", f"Changed: {label or wpath}")
                    if restart:
                        _set_status(activity=f"Restarting server for {label or wpath}…")
                        subprocess.Popen([sys.executable, __file__],
                                         cwd=os.path.dirname(os.path.abspath(__file__)))
                        WATCH_CONTROL["stop"] = True
                    c.execute("UPDATE file_watches SET last_mtime=? WHERE id=?", (mtime, wid))
            conn.commit()
            conn.close()
        except Exception as e:
            print("watcher error:", e)
        time.sleep(3)


@app.route('/watch', methods=['GET', 'POST'])
def watch():
    if request.method == 'GET':
        conn = sqlite3.connect('ace_memory.db')
        c = conn.cursor()
        c.execute("SELECT id, path, label, restart FROM file_watches")
        rows = [{"id": r[0], "path": r[1], "label": r[2], "restart": bool(r[3])} for r in c.fetchall()]
        conn.close()
        return jsonify({"watches": rows})
    data = request.json or {}
    wpath = data.get('path') or data.get('file')
    if not wpath:
        return jsonify({"error": "Missing path"}), 400
    if not os.path.exists(wpath):
        return jsonify({"error": f"Path not found: {wpath}"}), 400
    label = data.get('label') or os.path.basename(wpath)
    restart = bool(data.get('restart', False))
    mtime = os.path.getmtime(wpath)
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO file_watches (path, label, restart, last_mtime) VALUES (?,?,?,?)",
              (wpath, label, restart, mtime))
    conn.commit()
    wid = c.lastrowid
    conn.close()
    return jsonify({"success": True, "id": wid, "watch": {"path": wpath, "label": label, "restart": restart}})


@app.route('/watch/<int:wid>', methods=['DELETE'])
def watch_delete(wid):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("DELETE FROM file_watches WHERE id=?", (wid,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ──────────────────────────────────────────────────────────────
# Frontend compatibility endpoints
# ──────────────────────────────────────────────────────────────

@app.route('/notifications/pending', methods=['GET'])
def notifications_pending():
    after = request.args.get('after', '0')
    return jsonify({"notifications": [], "after": after})

# ──────────────────────────────────────────────────────────────
# Email notification endpoints
# ──────────────────────────────────────────────────────────────
@app.route('/email-notify/rules', methods=['GET'])
def email_notify_get_rules():
    rules = _load_email_notify_rules()
    return jsonify({"rules": rules})

@app.route('/email-notify/rules', methods=['POST'])
def email_notify_save_rules():
    data = request.get_json(silent=True) or {}
    rules = data.get('rules', [])
    _save_email_notify_rules(rules)
    return jsonify({"ok": True})

@app.route('/email-notify/test', methods=['POST'])
def email_notify_test():
    try:
        _show_windows_toast("ACEsi Test", "This is a test email notification from ACEsi.")
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ──────────────────────────────────────────────────────────────
# ntfy.sh push notifications (for phone)
# ──────────────────────────────────────────────────────────────
_NTFY_TOPIC = None

def _get_ntfy_topic():
    global _NTFY_TOPIC
    if _NTFY_TOPIC:
        return _NTFY_TOPIC
    # Generate a unique topic based on machine/user
    import hashlib, getpass, platform
    seed = f"{getpass.getuser()}-{platform.node()}"
    _NTFY_TOPIC = "acesi-" + hashlib.md5(seed.encode()).hexdigest()[:12]
    return _NTFY_TOPIC

@app.route('/notify/topic', methods=['GET'])
def notify_topic():
    return jsonify({"topic": _get_ntfy_topic()})

@app.route('/notify', methods=['POST'])
def notify_send():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or 'ACEsi').strip()
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({"error": "Message required"})
    topic = _get_ntfy_topic()
    try:
        # Send via ntfy.sh public server
        import urllib.parse, urllib.request
        url = f"https://ntfy.sh/{topic}"
        req = urllib.request.Request(
            url,
            data=message.encode('utf-8'),
            headers={
                'Title': title,
                'Priority': 'default',
                'Tags': 'bell',
            },
            method='POST'
        )
        urllib.request.urlopen(req, timeout=10)
        return jsonify({"ok": True, "topic": topic})
    except Exception as e:
        return jsonify({"error": str(e)})

# ──────────────────────────────────────────────────────────────
# Google Drive endpoints (REST API with existing token)
# ──────────────────────────────────────────────────────────────
_DRIVE_CREDENTIALS = os.path.join(os.path.dirname(__file__), "drive_credentials.json")
_DRIVE_TOKEN = os.path.join(os.path.dirname(__file__), "drive_token.json")
_DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"

def _load_drive_token():
    """Load and return the token data from drive_token.json."""
    if os.path.exists(_DRIVE_TOKEN):
        try:
            with open(_DRIVE_TOKEN, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"DEBUG: Failed to load token: {e}")
    return None

def _save_drive_token(token_data):
    """Save token data to drive_token.json."""
    try:
        with open(_DRIVE_TOKEN, 'w') as f:
            json.dump(token_data, f)
    except Exception as e:
        print(f"DEBUG: Failed to save token: {e}")

def _get_access_token():
    """Get a valid access token, refreshing if necessary."""
    token_data = _load_drive_token()
    if not token_data:
        return None, "No token file found"
    
    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token')
    expires_at = token_data.get('expires_at', 0)
    
    import time
    if time.time() < expires_at - 60:  # 60 second buffer
        return access_token, None
    
    # Token expired or about to expire, refresh it
    if not refresh_token:
        return None, "No refresh token available"
    
    if not os.path.exists(_DRIVE_CREDENTIALS):
        return None, "drive_credentials.json not found"
    
    try:
        with open(_DRIVE_CREDENTIALS, 'r') as f:
            creds = json.load(f)
        client_id = creds.get('client_id')
        client_secret = creds.get('client_secret')
    except Exception as e:
        return None, f"Failed to load credentials: {e}"
    
    if not client_id or not client_secret:
        return None, "Invalid credentials format"
    
    # Refresh the access token
    import requests
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    resp = requests.post(token_url, data=data, timeout=10)
    if resp.status_code != 200:
        return None, f"Token refresh failed: {resp.text}"
    
    new_token_data = resp.json()
    token_data['access_token'] = new_token_data['access_token']
    token_data['expires_at'] = time.time() + new_token_data.get('expires_in', 3600)
    _save_drive_token(token_data)
    return new_token_data['access_token'], None

def _drive_request(method, endpoint, access_token, **kwargs):
    """Make a request to the Google Drive API."""
    import requests
    url = f"{_DRIVE_API_BASE}{endpoint}"
    headers = {'Authorization': f'Bearer {access_token}'}
    if 'json' in kwargs:
        headers['Content-Type'] = 'application/json'
    resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    return resp

@app.route('/drive/status', methods=['GET'])
def drive_status():
    if not os.path.exists(_DRIVE_CREDENTIALS):
        return jsonify({"configured": False, "error": "drive_credentials.json not found"})
    # Check if we have a valid token
    access_token, err = _get_access_token()
    if err:
        return jsonify({"configured": True, "authorized": False})
    # Try to get user info
    user_info = {}
    try:
        resp = _drive_request('GET', '/about?fields=user(displayName,emailAddress)', access_token)
        if resp.status_code == 200:
            user_info = resp.json().get('user', {})
    except Exception:
        pass
    return jsonify({"configured": True, "authorized": True, "user": user_info})

@app.route('/drive/auth', methods=['GET'])
def drive_auth():
    access_token, err = _get_access_token()
    if not err:
        return jsonify({"ok": True, "message": "Already authenticated"})
    
    # Token refresh failed - need to re-authenticate
    if not os.path.exists(_DRIVE_CREDENTIALS):
        return jsonify({"ok": False, "error": "drive_credentials.json not found"}), 400
    
    try:
        with open(_DRIVE_CREDENTIALS, 'r') as f:
            creds = json.load(f)
        client_id = creds.get('client_id')
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
        scope = "https://www.googleapis.com/auth/drive"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return jsonify({
            "ok": False,
            "error": "Token expired or invalid. Please re-authenticate.",
            "auth_url": auth_url,
            "instructions": "1. Open the auth_url in your browser. 2. Sign in and grant permission. 3. Copy the authorization code. 4. POST it to /drive/auth with JSON {'code': '...'}"
        }), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route('/drive/auth', methods=['POST'])
def drive_auth_exchange():
    data = request.get_json(silent=True) or {}
    code = data.get('code')
    if not code:
        return jsonify({"ok": False, "error": "Authorization code required"}), 400
    
    if not os.path.exists(_DRIVE_CREDENTIALS):
        return jsonify({"ok": False, "error": "drive_credentials.json not found"}), 400
    
    try:
        with open(_DRIVE_CREDENTIALS, 'r') as f:
            creds = json.load(f)
        client_id = creds.get('client_id')
        client_secret = creds.get('client_secret')
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
        
        import requests
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        resp = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=10)
        if resp.status_code != 200:
            return jsonify({"ok": False, "error": resp.text}), 400
        
        token_data = resp.json()
        import time
        token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
        _save_drive_token(token_data)
        return jsonify({"ok": True, "message": "Authentication successful"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    if err:
        return jsonify({"ok": False, "error": err}), 400
    # If we get here, auth succeeded
    return jsonify({"ok": True, "message": "Authenticated successfully"})

def _drive_request(method, endpoint, access_token, **kwargs):
    """Make a request to the Google Drive API."""
    import requests
    url = f"{_DRIVE_API_BASE}{endpoint}"
    headers = {'Authorization': f'Bearer {access_token}'}
    if 'json' in kwargs:
        headers['Content-Type'] = 'application/json'
    resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    return resp

@app.route('/drive/list', methods=['GET'])
def drive_list():
    access_token, err = _get_access_token()
    if err:
        return jsonify({"ok": False, "error": err}), 400
    parent = request.args.get('parent', 'root')
    resp = _drive_request('GET', f"/files?q='{parent}'+in+parents+and+trashed=false&fields=files(id,name,mimeType,size,modifiedTime)&orderBy=folder,name&pageSize=200", access_token)
    if resp.status_code != 200:
        return jsonify({"ok": False, "error": resp.text}), 400
    data = resp.json()
    return jsonify({"ok": True, "files": data.get('files', []), "parent": parent})

@app.route('/drive/download', methods=['GET'])
def drive_download():
    file_id = request.args.get('id')
    if not file_id:
        return jsonify({"ok": False, "error": "File ID required"}), 400
    access_token, err = _get_access_token()
    if err:
        return jsonify({"ok": False, "error": err}), 400
    try:
        # Get file metadata
        meta_resp = _drive_request('GET', f"/files/{file_id}?fields=name,mimeType", access_token)
        if meta_resp.status_code != 200:
            return jsonify({"ok": False, "error": meta_resp.text}), 400
        file_meta = meta_resp.json()
        mime = file_meta.get('mimeType', '')
        name = file_meta.get('name', 'file')
        if mime == 'application/vnd.google-apps.folder':
            return jsonify({"ok": False, "error": "Cannot download a folder"}), 400
        
        # Export Google Workspace files
        if mime.startswith('application/vnd.google-apps.'):
            export_map = {
                'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            }
            export_mime = export_map.get(mime, 'application/pdf')
            resp = _drive_request('GET', f"/files/{file_id}/export?mimeType={export_mime}", access_token)
        else:
            resp = _drive_request('GET', f"/files/{file_id}?alt=media", access_token)
        
        if resp.status_code != 200:
            return jsonify({"ok": False, "error": resp.text}), 400
        
        return Response(resp.content, mimetype='application/octet-stream',
                        headers={'Content-Disposition': f'attachment; filename="{name}"'})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
        return Response(content, mimetype='application/octet-stream',
                        headers={'Content-Disposition': f'attachment; filename="{file_meta.get("name", "file")}"'})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route('/drive/upload', methods=['POST'])
def drive_upload():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    content = data.get('content')
    parent = data.get('parent', 'root')
    if not name or content is None:
        return jsonify({"ok": False, "error": "name and content required"}), 400
    access_token, err = _get_access_token()
    if err:
        return jsonify({"ok": False, "error": err}), 400
    try:
        import base64, io
        try:
            file_data = base64.b64decode(content)
        except Exception:
            file_data = content.encode('utf-8')
        
        # Create file metadata
        metadata = {'name': name}
        if parent != 'root':
            metadata['parents'] = [parent]
        
        # Upload using multipart upload
        import requests
        url = f"{_DRIVE_API_BASE}/files?uploadType=multipart"
        headers = {'Authorization': f'Bearer {access_token}'}
        files = {
            'metadata': ('metadata', json.dumps(metadata), 'application/json'),
            'file': (name, io.BytesIO(file_data), 'application/octet-stream')
        }
        resp = requests.post(url, headers={'Authorization': f'Bearer {access_token}'}, files=files, timeout=60)
        if resp.status_code not in (200, 201):
            return jsonify({"ok": False, "error": resp.text}), 400
        file_data = resp.json()
        return jsonify({"ok": True, "id": file_data.get('id'), "name": file_data.get('name')})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route('/whatsapp/send', methods=['POST'])
def whatsapp_send():
    data = request.get_json(silent=True) or {}
    phone = (data.get('phone') or '').strip()
    message = (data.get('message') or '').strip()
    if not phone:
        return jsonify({"ok": False, "error": "Phone number required"})
    if not message:
        return jsonify({"ok": False, "error": "Message required"})
    # WhatsApp Desktop (Microsoft Store) AppID
    app_id = "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
    import urllib.parse
    uri = f"whatsapp://send?phone={phone}&text={urllib.parse.quote(message)}"
    try:
        # Launch WhatsApp Desktop UWP app with the URI as argument
        subprocess.Popen(
            ['explorer.exe', f'shell:AppsFolder\\{app_id}', uri],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # Also show a Windows toast so you see it even if WhatsApp is slow
        _show_windows_toast("ACEsi → WhatsApp", f"Opening chat with {phone}: {message[:80]}")
        return jsonify({"ok": True, "reply": f"💬 WhatsApp opened for {phone} with your message."})
    except Exception as e:
        # Fallback: try generic URI handler
        try:
            subprocess.Popen(['cmd', '/c', 'start', '', uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return jsonify({"ok": True, "reply": f"💬 WhatsApp opened for {phone} with your message. (fallback)"})
        except Exception as e2:
            return jsonify({"ok": False, "error": f"UWP: {e}; fallback: {e2}"})

@app.route('/whatsapp/incoming', methods=['POST'])
def whatsapp_incoming():
    """
    Webhook for incoming WhatsApp messages forwarded from phone (Tasker/Shortcuts).
    Expected JSON: { "from": "27123456789", "name": "John", "message": "Hello" }
    """
    data = request.get_json(silent=True) or {}
    sender = (data.get('from') or data.get('phone') or '').strip()
    name = (data.get('name') or '').strip()
    message = (data.get('message') or data.get('body') or '').strip()
    if not sender or not message:
        return jsonify({"ok": False, "error": "Missing 'from' (phone) or 'message'"})
    display = name or sender
    title = f"💬 WhatsApp from {display}"
    body = message[:200]
    _show_windows_toast(title, body)
    # Also push to ACEsi chat via a simple mechanism - we can't directly push to WS,
    # but the user will see the toast. For chat, they'd need to refresh or we could
    # store in a queue. For now, just toast.
    return jsonify({"ok": True, "reply": f"📱 WhatsApp notification queued for {display}"})

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
    # Comment explains why use_reloader=False: reloader restart can deadlock
    # on the CDP/notification daemon threads ("Fatal Python error: _enter_buffered_busy").
    # Launch background daemon threads for scheduled tasks + file watching.
    threading.Thread(target=_scheduler_worker, daemon=True).start()
    threading.Thread(target=_watcher_worker, daemon=True).start()
    threading.Thread(target=_poll_email_notifications, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False,
            threaded=True)