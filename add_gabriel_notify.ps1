# add_gabriel_notify.ps1
# Adds Gabriel ntfy notification to ACEsi video tasks in server.py.
# Uses Python for safe exact-text editing (no line numbers, no raw \n mangling).
# Run: powershell -ExecutionPolicy Bypass -File add_gabriel_notify.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "add_gabriel_notify.py"

# Write the Python edit script inline
@'
import py_compile
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\server.py"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

edits = []

# Edit 1: Gabriel topic constant
edits.append((r'''NTFY_TOPIC = "ACEsi0102"
NTFY_INBOUND_PASSPHRASE = "acesi0102"
NTFY_SERVER = "https://ntfy.sh"''',
r'''NTFY_TOPIC = "ACEsi0102"
NTFY_INBOUND_PASSPHRASE = "acesi0102"
NTFY_SERVER = "https://ntfy.sh"
# Gabriel's ntfy topic (Chris's son). Put Gabriel's topic id in
# ntfy_gabriel_topic.txt (gitignored) next to this file, or edit the
# constant below. The ntfy app on Gabriel's phone must subscribe to it.
_NTFY_GABRIEL_TOPIC_FILE = "ntfy_gabriel_topic.txt"
try:
    with open(_NTFY_GABRIEL_TOPIC_FILE, "r", encoding="utf-8") as _gf:
        NTFY_TOPIC_GABRIEL = _gf.read().strip() or None
except Exception:
    NTFY_TOPIC_GABRIEL = None'''))

# Edit 2: Extend send_ntfy() + add send_ntfy_gabriel()
edits.append((r'''def send_ntfy(title, message):
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
        return False''',
r'''def send_ntfy(title, message, topic=None):
    """Send a push notification via ntfy.
    topic=None -> Chris's topic (NTFY_TOPIC). Pass Gabriel's topic id to notify him."""
    try:
        target_topic = topic or NTFY_TOPIC
        # Titles travel as an HTTP header, which requests encodes as latin-1, so
        # an em-dash in a title (e.g. "ACEsi — Email alert") used to raise
        # UnicodeEncodeError and the phone never got the alert. Keep the title
        # ASCII (or percent-encode) and put the readable text in the body, which
        # is sent as UTF-8 bytes and has no such limit.
        safe_title = str(title).encode("ascii", "replace").decode("ascii")
        r = requests.post(
            f"{NTFY_SERVER}/{target_topic}",
            data=str(message).encode('utf-8'),
            headers={"Priority": "high", "Title": safe_title},
            timeout=10
        )
        _record_self_ntfy_id(r)
        return True
    except Exception as e:
        print(f"⚠️ ntfy error: {e}")
        return False


def send_ntfy_gabriel(message, title="ACEsi"):
    """Send a push notification to Gabriel's ntfy topic.
    Returns True on success. Gabriel's ntfy app must be subscribed to
    NTFY_TOPIC_GABRIEL (see ntfy_gabriel_topic.txt)."""
    if not NTFY_TOPIC_GABRIEL:
        print("⚠️ Gabriel ntfy topic not configured (ntfy_gabriel_topic.txt)")
        return False
    return send_ntfy(title, message, topic=NTFY_TOPIC_GABRIEL)'''))

# Edit 3: Add tool_notify_gabriel()
edits.append((r'''def tool_notify(title="ACEsi", message="Ping from ACEsi"):
    """Send a push notification (ntfy) to Chris's phone. Returns (ok, result).
    Args: title (optional, default 'ACEsi'), message (optional).
    NOTE: ntfy requires the ntfy app on the phone subscribing to NTFY_TOPIC."""
    if not message or not str(message).strip():
        return False, "notify usage: message=<text> [title=<title>]"
    ok = send_ntfy(str(title), str(message))
    return (True, f"Notified '{title}': {str(message)[:80]}" if ok
            else (False, "ntfy push failed (check internet / ntfy app subscription)"))''',
r'''def tool_notify(title="ACEsi", message="Ping from ACEsi"):
    """Send a push notification (ntfy) to Chris's phone. Returns (ok, result).
    Args: title (optional, default 'ACEsi'), message (optional).
    NOTE: ntfy requires the ntfy app on the phone subscribing to NTFY_TOPIC."""
    if not message or not str(message).strip():
        return False, "notify usage: message=<text> [title=<title>]"
    ok = send_ntfy(str(title), str(message))
    return (True, f"Notified '{title}': {str(message)[:80]}" if ok
            else (False, "ntfy push failed (check internet / ntfy app subscription)"))


def tool_notify_gabriel(title="ACEsi", message="Ping from ACEsi"):
    """Send a push notification (ntfy) to Gabriel's phone. Returns (ok, result).
    Args: title (optional, default 'ACEsi'), message (optional).
    NOTE: Gabriel's ntfy app must be subscribed to NTFY_TOPIC_GABRIEL."""
    if not NTFY_TOPIC_GABRIEL:
        return False, "Gabriel ntfy topic not configured (ntfy_gabriel_topic.txt)"
    if not message or not str(message).strip():
        return False, "notify usage: message=<text> [title=<title>]"
    ok = send_ntfy(str(title), str(message), topic=NTFY_TOPIC_GABRIEL)
    return (True, f"Notified Gabriel '{title}': {str(message)[:80]}" if ok
            else (False, "ntfy push to Gabriel failed (check internet / subscription)"))'''))

# Edit 4: Register in tools dict
edits.append((r'''    "notify": (tool_notify, ("title", "message")),''',
r'''    "notify": (tool_notify, ("title", "message")),
    "notify_gabriel": (tool_notify_gabriel, ("title", "message")),'''))

# Edit 5: Schema entry #1
edits.append((r'''    {"type": "function", "function": {"name": "notify",
        "description": "Send a push notification to Chris's phone via ntfy. Use for pings, alerts, reminders, or any 'notify me / ping my phone / tell me when' request. Args: title (optional, default 'ACEsi'), message (optional text to send). NOTE: Chris's phone must have the ntfy app installed and subscribed to this server's private topic.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "title": "title", "description": "Optional. Notification title, default 'ACEsi'."},
            "message": {"type": "string", "title": "message", "description": "Optional. The message text to push. Default 'Ping from ACEsi'."}},
            "required": []}}},''',
r'''    {"type": "function", "function": {"name": "notify",
        "description": "Send a push notification to Chris's phone via ntfy. Use for pings, alerts, reminders, or any 'notify me / ping my phone / tell me when' request. Args: title (optional, default 'ACEsi'), message (optional text to send). NOTE: Chris's phone must have the ntfy app installed and subscribed to this server's private topic.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "title": "title", "description": "Optional. Notification title, default 'ACEsi'."},
            "message": {"type": "string", "title": "message", "description": "Optional. The message text to push. Default 'Ping from ACEsi'."}},
            "required": []}}},
    {"type": "function", "function": {"name": "notify_gabriel",
        "description": "Send a push notification to Gabriel's phone via ntfy. Use when Chris asks to notify Gabriel. Args: title (optional, default 'ACEsi'), message (optional text to send). NOTE: Gabriel's ntfy app must be subscribed to the topic in ntfy_gabriel_topic.txt.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "title": "title", "description": "Optional. Notification title, default 'ACEsi'."},
            "message": {"type": "string", "title": "message", "description": "Optional. The message text to push. Default 'Ping from ACEsi'."}},
            "required": []}}},'''))

# Edit 6: Schema entry #2
edits.append((r'''    {"type": "function", "function": {"name": "notify",
        "description": "Send a push notification to Chris's phone via ntfy. Use when Chris asks to 'ping my phone', 'notify me'. Args: message (text), title optional.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},''',
r'''    {"type": "function", "function": {"name": "notify",
        "description": "Send a push notification to Chris's phone via ntfy. Use when Chris asks to 'ping my phone', 'notify me'. Args: message (text), title optional.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "notify_gabriel",
        "description": "Send a push notification to Gabriel's phone via ntfy. Args: message (text), title optional.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},'''))

# Edit 7: Schema entry #3
edits.append((r'''    {"type": "function", "function": {"name": "notify",
        "description": "Send push notification via ntfy. Args: message, title.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},''',
r'''    {"type": "function", "function": {"name": "notify",
        "description": "Send push notification via ntfy. Args: message, title.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},
    {"type": "function", "function": {"name": "notify_gabriel",
        "description": "Send push notification to Gabriel via ntfy. Args: message, title.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "message": {"type": "string"}}, "required": ["message"]}}},'''))

# Edit 8: Icon
edits.append((r'''    "run_command": "▶", "notify": "🔔", "web_search": "🔎", "webfetch": "🌐",''',
r'''    "run_command": "▶", "notify": "🔔", "notify_gabriel": "👨‍👦", "web_search": "🔎", "webfetch": "🌐",'''))

# Edit 9: Domain
edits.append((r'''    # push notification to Chris's phone (available in every domain, like ctrl)
    "notify": "ctrl",''',
r'''    # push notification to Chris's phone (available in every domain, like ctrl)
    "notify": "ctrl",
    # push notification to Gabriel's phone (available in every domain, like ctrl)
    "notify_gabriel": "ctrl",'''))

# Edit 10: Core tools
edits.append((r'''    "open_in_vscode", "edit_file", "get_notifications", "check_email", "notify",''',
r'''    "open_in_vscode", "edit_file", "get_notifications", "check_email", "notify", "notify_gabriel",'''))

# Edit 11: Wire into _ffmpeg_video_reply
edits.append((r'''    if ok and (made or clips_now):
        extra = ""
        if mode == "stream copy":
            extra = ("\n(Stream copy is fast but cuts land on keyframes, so a clip "
                     "can be a little longer than %ss.)" % secs_txt)
        return ("Split `%s` into %s-second clips%s using %s.\n"
                "Created %d file(s):\n%s%s") % (
                    os.path.basename(src), secs_txt, note, mode,
                    len(made or clips_now), listing, extra)''',
r'''    if ok and (made or clips_now):
        extra = ""
        if mode == "stream copy":
            extra = ("\n(Stream copy is fast but cuts land on keyframes, so a clip "
                     "can be a little longer than %ss.)" % secs_txt)
        reply = ("Split `%s` into %s-second clips%s using %s.\n"
                "Created %d file(s):\n%s%s") % (
                    os.path.basename(src), secs_txt, note, mode,
                    len(made or clips_now), listing, extra)
        # Notify Gabriel when a video task completes
        try:
            send_ntfy_gabriel(
                "Video task complete",
                "Gabriel Video task complete — click here")
        except Exception:
            pass
        return reply'''))

# Edit 12: Wire into _youtube_reply (download only)
edits.append((r'''    if not want_split or not secs:
        size_mb = os.path.getsize(target) / (1024.0 * 1024.0)
        return "Downloaded `%s`%s.\n- %s (%.1f MB)" % (
            os.path.basename(target), note, target, size_mb)''',
r'''    if not want_split or not secs:
        size_mb = os.path.getsize(target) / (1024.0 * 1024.0)
        reply = "Downloaded `%s`%s.\n- %s (%.1f MB)" % (
            os.path.basename(target), note, target, size_mb)
        # Notify Gabriel when a video task completes
        try:
            send_ntfy_gabriel(
                "Video task complete",
                "Gabriel Video task complete — click here")
        except Exception:
            pass
        return reply'''))

# Edit 13: Wire into _youtube_reply (download + split)
edits.append((r'''    split_reply = _ffmpeg_video_reply(
        'split "%s" into %g-second clips' % (target, secs))
    head = "Downloaded `%s`%s.\n\n" % (os.path.basename(target), note)
    return head + (split_reply or "Download finished, but the split didn't run.")''',
r'''    split_reply = _ffmpeg_video_reply(
        'split "%s" into %g-second clips' % (target, secs))
    head = "Downloaded `%s`%s.\n\n" % (os.path.basename(target), note)
    reply = head + (split_reply or "Download finished, but the split didn't run.")
    # Notify Gabriel when a video task completes
    try:
        send_ntfy_gabriel(
            "Video task complete",
            "Gabriel Video task complete — click here")
    except Exception:
        pass
    return reply'''))

for i, (old, new) in enumerate(edits, 1):
    count = text.count(old)
    if count == 0:
        print(f"EDIT {i}: FAILED — old text not found")
        print("--- start ---")
        print(old[:200])
        print("--- end ---")
        sys.exit(1)
    elif count > 1:
        print(f"EDIT {i}: FAILED — old text found {count} times (ambiguous)")
        sys.exit(1)
    text = text.replace(old, new, 1)
    print(f"EDIT {i}: OK")

with open(SERVER, "w", encoding="utf-8-sig", newline="") as f:
    f.write(text.replace("\n", "\r\n"))

try:
    py_compile.compile(SERVER, doraise=True)
    print("\nCompile check: COMPILES OK")
except py_compile.PyCompileError as e:
    print(f"\nCompile check: FAILED — {e}")
    sys.exit(1)

with open(SERVER, "rb") as f:
    raw = f.read()
bare_lf = raw.count(b"\n") - raw.count(b"\r\n")
print(f"Bare LF count: {bare_lf}")
print("\nAll edits applied successfully.")
'@ | Set-Content -Path $pyScript -Encoding UTF8

# Run the Python edit script
python $pyScript

# Add ntfy_gabriel_topic.txt to .gitignore if not already present
$gitignore = Join-Path $scriptDir ".gitignore"
$gi = Get-Content $gitignore -Raw
if ($gi -notmatch "ntfy_gabriel_topic\.txt") {
    $gi = $gi -replace "ntfy_topic\.txt`n", "ntfy_topic.txt`nntfy_gabriel_topic.txt`n"
    $gi | Set-Content -Path $gitignore -Encoding UTF8
    Write-Host "Added ntfy_gabriel_topic.txt to .gitignore"
} else {
    Write-Host "ntfy_gabriel_topic.txt already in .gitignore"
}

# Compile check
python -c "import py_compile; py_compile.compile('server.py', doraise=True); print('Final compile: OK')"

Write-Host "`nDone. Next step: create ntfy_gabriel_topic.txt with Gabriel's ntfy topic id."
