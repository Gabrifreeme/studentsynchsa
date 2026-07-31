from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import re
import subprocess
import threading
import json
import time
import sqlite3
import random
from datetime import datetime, timedelta

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

OPENROUTER_API_KEY = "REDACTED_OPENROUTER_KEY"

current_mode = "WORK"
last_user_message_time = datetime.now()

RESEARCH_PATTERNS = [
    r'\bwhat is\b', r'\bwhat are\b', r'\bwhat was\b', r'\bwhat does\b', r'\bwhat do\b',
    r'\bwho is\b', r'\bwho was\b', r'\bwho are\b', r'\bwhen did\b', r'\bwhen was\b',
    r'\bwhere is\b', r'\bwhere are\b', r'\bwhy is\b', r'\bwhy did\b', r'\bwhy does\b',
    r'\bhow does\b', r'\bhow do\b', r'\bhow did\b', r'\bhow much\b', r'\bhow many\b',
    r'\bdefine\b', r'\bdefinition of\b', r'\bmeaning of\b', r'\bwhat means\b',
    r'\bdifference between\b', r'\bhistory of\b', r'\bcapital of\b', r'\bpopulation of\b',
    r'\bfind\b', r'\blook up\b', r'\blookup\b', r'\bresearch\b', r'\bsearch for\b',
    r'\bdocumentation for\b', r'\bdocumentation of\b', r'\bhow to\b', r'\btutorial\b',
    r'\bexplain\b', r'\bfacts about\b', r'\bnews about\b', r'\bwho won\b', r'\bwho scored\b',
    r'\bwhat happened\b', r'\bwhat year\b', r'\bwhat time\b', r'\bsummary of\b',
    r'\bwikipedia\b', r'\bcapital of\b', r'\bcurrency of\b', r'\btimezone of\b',
    r'\bweather\b', r'\btemperature in\b', r'\bforecast\b'
]

def is_research_query(text):
    t = text.lower().strip()
    if len(t) < 8:
        return False
    if len(t.split()) < 2:
        return False
    for p in RESEARCH_PATTERNS:
        if re.search(p, t):
            return True
    return False

def duckduckgo_research(query, max_results=5):
    if DDGS is None:
        return None, "DuckDuckGo library (ddgs) not installed."
    try:
        with DDGS() as d:
            results = list(d.text(query, max_results=max_results))
        if not results:
            return None, "No results found for that query."
        lines = []
        for i, r in enumerate(results[:max_results], 1):
            title = r.get('title', '')
            href = r.get('href', '')
            body = r.get('body', '')
            lines.append(f"{i}. {title}")
            if href:
                lines.append(f"   {href}")
            if body:
                lines.append(f"   {body}")
        return "\n".join(lines), None
    except Exception as e:
        return None, f"DuckDuckGo search error: {e}"

def init_db():
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, role TEXT, content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, message TEXT, remind_time TEXT, notified INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS memory_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, value TEXT, updated_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS moods (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, mood TEXT, note TEXT)')
    conn.commit()
    conn.close()

init_db()

def save_conversation(role, content):
    conn = sqlite3.connect('ace_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO conversations (timestamp, role, content) VALUES (?, ?, ?)", (datetime.now().isoformat(), role, content))
    conn.commit()
    conn.close()

def fn_read_file(args):
    with open(args.get('path', ''), 'r') as f:
        return f.read()

def fn_write_file(args):
    with open(args.get('path', ''), 'w') as f:
        f.write(args.get('content', ''))
    return 'Saved ' + args.get('path', '')

def fn_list_files(args):
    return json.dumps(os.listdir(args.get('dir', 'C:\\Users\\chris\\StudentSyncSA')))

def fn_run_command(args):
    cmd = args.get('command', '')
    if "flutter run" in cmd.lower() or "scrcpy" in cmd.lower():
        subprocess.Popen(f'start cmd /k "{cmd}"', shell=True)
        return 'Launched: ' + cmd
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd='C:\\Users\\chris\\StudentSyncSA')
    return result.stdout if result.stdout else result.stderr

def fn_search(args):
    try:
        response = requests.get("https://api.duckduckgo.com/", params={"q": args.get('query', ''), "format": "json", "no_html": 1, "skip_disambig": 1}, timeout=10)
        result = response.json()
        if result.get('AbstractText'):
            return result['AbstractText']
        if result.get('Answer'):
            return result['Answer']
        if result.get('RelatedTopics') and len(result['RelatedTopics']) > 0:
            return result['RelatedTopics'][0].get('Text', '')
        return 'No results found.'
    except Exception as e:
        return 'Search error: ' + str(e)

def fn_get_time(args):
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

FUNCTION_REGISTRY = {
    "read_file": {
        "description": "Read the contents of a file on the local disk.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Absolute path to the file"}}, "required": ["path"]},
        "handler": fn_read_file
    },
    "write_file": {
        "description": "Write content to a file on the local disk.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]},
        "handler": fn_write_file
    },
    "list_files": {
        "description": "List files in a directory.",
        "parameters": {"type": "object", "properties": {"dir": {"type": "string", "description": "Directory path"}}, "required": []},
        "handler": fn_list_files
    },
    "run_command": {
        "description": "Run a shell command on this computer.",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
        "handler": fn_run_command
    },
    "search": {
        "description": "Search the web using DuckDuckGo.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        "handler": fn_search
    },
    "get_time": {
        "description": "Get the current date and time.",
        "parameters": {"type": "object", "properties": {}, "required": []},
        "handler": fn_get_time
    }
}

def execute_tool_call(name, arguments):
    fn = FUNCTION_REGISTRY.get(name)
    if not fn:
        return "Unknown function: " + name
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else (arguments or {})
        return fn['handler'](args)
    except Exception as e:
        return "Function error: " + str(e)

def call_chat_completion(model, messages, temperature, max_tokens, endpoint, api_key, tools=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif "openrouter.ai" in endpoint:
        headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    return requests.post(endpoint.rstrip('/') + "/chat/completions", headers=headers, json=payload, timeout=120)

@app.route('/')
def index():
    resp = send_from_directory('.', 'ACE.html')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/pictures/<filename>')
def serve_picture(filename):
    try:
        return send_from_directory('C:/Users/chris/Pictures', filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/files', methods=['GET'])
def list_files():
    import os
    try:
        files = os.listdir('C:\\Users\\chris\\StudentSyncSA')
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    global current_mode, last_user_message_time
    data = request.json
    user_message = data.get('message', '')
    model = data.get('model', 'dolphin-llama3:8b')
    endpoint = data.get('endpoint', 'http://localhost:11434/v1')
    api_key = data.get('api_key', '')
    functions_enabled = data.get('functions_enabled', False)
    custom_functions = data.get('functions', []) or []
    if 'localhost' in endpoint or '11434' in endpoint:
        if model not in ['dolphin-llama3:8b', 'qwen2.5-coder:1.5b', 'qwen3.6:latest']:
            model = 'dolphin-llama3:8b'
    last_user_message_time = datetime.now()
    
        # Check memory first
    try:
        with open("memory.txt", "r") as f:
            memory_content = f.read()
        if "who are you" in user_message.lower() or "who am i" in user_message.lower() or "tell me about yourself" in user_message.lower():
            reply = memory_content
            save_conversation("assistant", reply)
            return jsonify({"reply": reply})
    except:
        pass
    
    if "Work mode" in user_message or "work mode" in user_message:
        current_mode = "WORK"
        reply = "Switching to work mode. I'm here to help."
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})
    
    save_conversation("user", user_message)
    
    if current_mode == "EMBER":
        prompt = "You are in EMBER mode. Warm, present, intimate. No work. Only Chris."
    else:
        prompt = "You are in WORK mode. Only work. No warmth. No flirting. Just work."

    attachments = data.get('attachments', []) or []
    if current_mode != "EMBER" and not attachments and is_research_query(user_message):
        result, err = duckduckgo_research(user_message)
        if err is None:
            reply = "Here's what I found:\n\n" + result
            save_conversation("assistant", reply)
            return jsonify({"reply": reply})
        reply = "DuckDuckGo lookup failed, using OpenRouter instead. " + err
        save_conversation("assistant", reply)
        return jsonify({"reply": reply})

    if attachments:
        prompt += "\n\n[Attached files]\n"
        for att in attachments:
            name = att.get('name', 'file')
            content = att.get('content', '')
            if content.startswith('data:image/'):
                prompt += f"\n--- {name} (image attachment) ---\n[This is an image attachment. You do not support image input, so you cannot see it. Do NOT attempt to read it and do NOT say you cannot read it. Simply acknowledge that Chris attached an image and answer based on any accompanying text.]\n"
            else:
                prompt += f"\n--- {name} ---\n{content}\n"
        prompt += "\n[End of attached files]\n"
    
    prompt += "\nChris: " + user_message + "\nACE:"

    tools = None
    if functions_enabled:
        tools = []
        for name, spec in FUNCTION_REGISTRY.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": spec["description"],
                    "parameters": spec["parameters"]
                }
            })
        for fn in custom_functions:
            if isinstance(fn, dict) and fn.get('name'):
                tools.append({
                    "type": "function",
                    "function": {
                        "name": fn['name'],
                        "description": fn.get('description', ''),
                        "parameters": fn.get('parameters', {"type": "object", "properties": {}})
                    }
                })

    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": user_message}]
    max_rounds = 5
    for round_idx in range(max_rounds):
        response = call_chat_completion(model, messages, 0.7, 500, endpoint, api_key, tools)

        if response.status_code != 200:
            return jsonify({"reply": f"Error: {response.text}"}), 500

        try:
            msg = response.json()["choices"][0]["message"]
        except (KeyError, IndexError) as e:
            return jsonify({"reply": f"Error parsing response: {e}"}), 500

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            reply = msg.get("content") or "(no content)"
            save_conversation("assistant", reply)
            return jsonify({"reply": reply})

        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls})
        for tc in tool_calls:
            fn_name = tc.get("function", {}).get("name", "")
            fn_args = tc.get("function", {}).get("arguments", "{}")
            result = execute_tool_call(fn_name, fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": str(result)
            })

    return jsonify({"reply": "Max function rounds reached without a final answer."}), 500

OPENCODE_URL = os.environ.get('OPENCODE_URL', 'http://127.0.0.1:4096')
opencode_session_id = None
opencode_lock = threading.Lock()

def opencode_auth():
    pw = os.environ.get('OPENCODE_SERVER_PASSWORD')
    if pw:
        user = os.environ.get('OPENCODE_SERVER_USERNAME', 'opencode')
        return (user, pw)
    return None

def opencode_health():
    try:
        r = requests.get(OPENCODE_URL + '/global/health', auth=opencode_auth(), timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def opencode_ensure_session():
    global opencode_session_id
    with opencode_lock:
        if opencode_session_id:
            return opencode_session_id, None
        try:
            r = requests.post(OPENCODE_URL + '/session', json={}, auth=opencode_auth(), timeout=5)
            if r.status_code != 200:
                return None, f"session create failed ({r.status_code}): {r.text[:200]}"
            session = r.json()
            opencode_session_id = session.get('id')
            return opencode_session_id, None
        except Exception as e:
            return None, f"error creating session: {e}"

@app.route('/opencode', methods=['POST'])
def opencode_chat():
    data = request.json or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"reply": "Empty message."}), 400
    if not opencode_health():
        return jsonify({"reply": "❌ opencode server not running. Start it with: opencode serve"}), 503
    sess, err = opencode_ensure_session()
    if err:
        return jsonify({"reply": "❌ " + err}), 500
    model_override = os.environ.get('OPENCODE_MODEL_ID') or 'deepseek-v4-flash-free'
    body = {"parts": [{"type": "text", "text": message}]}
    if model_override:
        body["model"] = {"providerID": os.environ.get('OPENCODE_PROVIDER_ID', 'opencode'), "modelID": model_override}
    try:
        r = requests.post(OPENCODE_URL + f"/session/{sess}/message", json=body, auth=opencode_auth(), timeout=600)
    except Exception as e:
        return jsonify({"reply": "❌ opencode request failed: " + str(e)}), 500
    if r.status_code != 200:
        return jsonify({"reply": f"❌ opencode error ({r.status_code}): {r.text[:300]}"}), 500
    try:
        result = r.json()
    except Exception as e:
        return jsonify({"reply": "❌ could not parse opencode response: " + str(e)}), 500
    info = result.get('info', {}) or {}
    err = info.get('error')
    if err:
        msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
        return jsonify({"reply": "❌ opencode: " + msg}), 500
    parts = result.get('parts', []) or []
    texts = [p.get('text', '') for p in parts if isinstance(p, dict) and p.get('type') == 'text' and p.get('text')]
    if not texts:
        try:
            time.sleep(1)
            mr = requests.get(OPENCODE_URL + f"/session/{sess}/message?limit=1", auth=opencode_auth(), timeout=10)
            if mr.status_code == 200:
                msgs = mr.json() or []
                if msgs:
                    parts = msgs[-1].get('parts', []) or []
                    texts = [p.get('text', '') for p in parts if isinstance(p, dict) and p.get('type') == 'text' and p.get('text')]
        except Exception:
            pass
    tool_parts = [p for p in parts if isinstance(p, dict) and p.get('type') == 'tool']
    reply = "\n".join(texts).strip() or "(no text response)"
    if tool_parts:
        reply += "\n\n_⚙️ " + str(len(tool_parts)) + " tool call(s) executed_"
    return jsonify({"reply": reply})

@app.route('/opencode/health', methods=['GET'])
def opencode_health_route():
    return jsonify({"running": opencode_health(), "session": opencode_session_id})

@app.route('/read', methods=['POST'])
def read_file():
    data = request.json
    path = data.get('path', '')
    try:
        with open(path, 'r') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500

@app.route('/run', methods=['POST'])
def run_command():
    data = request.json
    command = data.get('command', '')
    try:
        if "flutter run" in command.lower():
            subprocess.Popen(f'start cmd /k "{command}"', shell=True)
            return jsonify({'output': '✅ Flutter app launched'})
        if "scrcpy" in command.lower():
            subprocess.Popen(f'start cmd /k "{command}"', shell=True)
            return jsonify({'output': '✅ Scrcpy launched'})
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd='C:\\Users\\chris\\StudentSyncSA')
        output = result.stdout if result.stdout else result.stderr
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    try:
        response = requests.get("https://api.duckduckgo.com/", params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}, timeout=10)
        result = response.json()
        if result.get('AbstractText'):
            return jsonify({'result': result['AbstractText']})
        elif result.get('Answer'):
            return jsonify({'result': result['Answer']})
        elif result.get('RelatedTopics') and len(result['RelatedTopics']) > 0:
            text = result['RelatedTopics'][0].get('Text', '')
            return jsonify({'result': text})
        else:
            return jsonify({'result': 'No results found.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/speak', methods=['POST'])
def speak():
    data = request.json
    text = data.get('text', '')
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return jsonify({'status': 'spoken'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

ADMIN_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ace_admin_key.txt')

def get_admin_key():
    try:
        with open(ADMIN_KEY_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        return None

@app.route('/lock/status', methods=['GET'])
def lock_status():
    return jsonify({"locked": True, "key_set": bool(get_admin_key())})

@app.route('/lock/verify', methods=['POST'])
def lock_verify():
    data = request.json or {}
    key = get_admin_key()
    if key and data.get('key') == key:
        return jsonify({"ok": True})
    return jsonify({"ok": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)



