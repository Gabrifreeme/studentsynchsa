# devtools_service.py
# Chrome DevTools Protocol bridge for ACEsi.
#
# Connects to a running WebView / Chrome devtools target (local Chrome via
# http://localhost:PORT/json, or an Android app WebView via adb forward to its
# webview_devtools_remote_<pid> socket) and exposes:
#   get_console_logs()    -> buffered Runtime.consoleAPICalled events
#   get_network_requests() -> buffered Network.requestWillBeSent/responseReceived
#   get_dom_state()        -> current DOM snapshot (title/url/outerHTML)
#   evaluate_js(expr)      -> run JS in the page, return its value
#
# Config (env):
#   ACE_CDP_BROWSER_WS   : explicit ws URL of a browser target (skip discovery)
#   ACE_CDP_URL_FRAGMENT : pick the page target whose url/title contains this
#                          (e.g. "univen", "ITS_OAP"); else first page target
#   ACE_CDP_PORT         : preferred local discovery port (e.g. 9230)
#   ACE_DEVICE_SERIAL    : adb serial (else first online device)
#   ACE_DEVICE_PACKAGE   : app package for adb forward discovery

import os, sys, json, time, threading, subprocess, re
import urllib.request
import websocket

# ── Context-aware app package ──────────────────────────────────────────────
# ACEsi is a general-purpose agent framework. The Android app to talk to is
# resolved from the active Context (ace_context.py). Falls back to the legacy
# hardcoded package for backward compatibility.
try:
    import ace_context as _ctx
    def _app_package():
        c = _ctx.get_active_context()
        if c and c.get("app_package"):
            return c["app_package"]
        return "com.studentsyncsa.studentsyncsa"
except Exception:
    def _app_package():
        return "com.studentsyncsa.studentsyncsa"

APP_PACKAGE = _app_package()  # legacy constant for backward compat
DEFAULT_FORWARD_PORT = 9229
SCAN_PORTS = [9230, 9222, 9229, 9223, 9225]

_lock = threading.RLock()
_session = None
_session_lock = threading.Lock()
# Why the last WebSocket connect attempt failed (empty = no failure). Kept so a
# failed cdp_connect reports a real cause rather than a generic message.
_LAST_CONNECT_ERROR = ""


def _env(name, default=""):
    return os.environ.get(name) or default


def _device_serial():
    s = _env("ACE_DEVICE_SERIAL")
    if s:
        return s
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True,
                             timeout=10, creationflags=_NO_WINDOW).stdout
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                return parts[0]
    except Exception:
        pass
    return "A6FF6R5527000712"  # fallback to known device


_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def set_context(name):
    """Delegate to ace_context.set_active_context — switching the active
    context also invalidates any cached CDP session so the next call to
    _get_session re-discovers the correct target for the new context."""
    global _session
    try:
        import ace_context
        changed = ace_context.set_active_context(name)
        if changed:
            _session = None  # force re-discover target
        return True, changed
    except Exception as e:
        return False, str(e)


def current_app_package():
    """Public accessor for the currently resolved app package."""
    return _app_package()


def _adb(*args, timeout=15):
    try:
        r = subprocess.run(["adb", "-s", _device_serial(), *args],
                           capture_output=True, text=True, timeout=timeout,
                           creationflags=_NO_WINDOW)
        return r.stdout
    except Exception as e:
        return ""


def _list_targets(port):
    """GET /json/list, trying IPv4 then IPv6. Returns list or None."""
    for host in ("127.0.0.1", "[::1]"):
        try:
            with urllib.request.urlopen(f"http://{host}:{port}/json/list", timeout=4) as r:
                if r.status == 200:
                    return json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            continue
    return None


def _discover_socket_names():
    """Return devtools socket names from the device's /proc/net/unix."""
    out = _adb("shell", "cat /proc/net/unix")
    names = set()
    for line in out.splitlines():
        if "devtools_remote" in line:
            tok = line.split()[-1]
            if tok.startswith("@"):
                names.add(tok[1:])
            names.add(tok)
    return sorted(names)


def _adb_forward(name, port):
    """Forward tcp:port -> local:<name>, trying plain, @ (abstract) and
    localabstract: forms. Android WebView devtools sockets are abstract unix
    sockets and REQUIRE the localabstract: prefix."""
    _adb("forward", "--remove", f"tcp:{port}")
    for form in (f"local:{name}", f"local:@{name}",
                 f"localabstract:{name}", f"localabstract:@{name}"):
        _adb("forward", f"tcp:{port}", form)
        t = _list_targets(port)
        if t is not None:
            return True
    return False


def _app_pid():
    pkg = _app_package()
    out = _adb("shell", "pidof " + pkg)
    tok = (out or "").split()
    return tok[0] if tok else None


def _cdp_url_fragment():
    """Return the URL/title fragment used to select the right browser/WebView tab.
    Reads from the active Context; falls back to the ACE_CDP_URL_FRAGMENT env var."""
    try:
        c = _ctx.get_active_context()
        if c and c.get("cdp_url_fragment"):
            return c["cdp_url_fragment"]
    except Exception:
        pass
    return _env("ACE_CDP_URL_FRAGMENT", "")


def _select_target(targets):
    """Pick the best CDP target: prefer a 'page' whose url/title matches the
    configured fragment, else the first page, else any debuggable target.

    NOTE: this is deliberately an explicit loop and NOT a list comprehension.
    The comprehension form of this exact function miscompiles and silently
    yields an EMPTY list for valid page targets, which made cdp_connect fail
    against a perfectly healthy browser (targets were present on /json/list the
    whole time). Reproduced on CPython 3.11 and 3.14. Do not "simplify" this
    back into `[t for t in targets if ...]`.
    """
    frag = _cdp_url_fragment().lower() if _cdp_url_fragment() else ""
    pages = []
    for t in targets:
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            pages.append(t)
    if frag:
        # Support | as OR (e.g. "univen|ITS_OAP")
        frags = frag.split("|")
        for t in pages:
            u = ((t.get("url") or "") + " " + (t.get("title") or "")).lower()
            if any(f and f in u for f in frags):
                return t
    if pages:
        return pages[0]
    for t in targets:
        if t.get("webSocketDebuggerUrl"):
            return t
    return None



def restart_local_chrome():
    """Kill any Chrome on the CDP port (and drop the session), then relaunch it."""
    global _session
    try:
        _session = None
        r = subprocess.run("netstat -ano", shell=True, capture_output=True,
                           text=True, timeout=30, creationflags=_NO_WINDOW)
        pids = set()
        for line in r.stdout.splitlines():
            if "127.0.0.1:9230" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    pids.add(parts[-1])
        for p in pids:
            try:
                subprocess.run("taskkill /F /PID %s" % p, shell=True,
                               capture_output=True, text=True, timeout=30,
                               creationflags=_NO_WINDOW)
            except Exception:
                pass
        time.sleep(1)
    except Exception:
        pass
    return _ensure_local_browser()


def _ensure_local_browser():
    """If no local Chrome/Chromium devtools server is reachable on the default port,
    launch a detached headless Chrome with --remote-allow-origins=* so WebSocket
    connections are accepted (Chrome 115+ otherwise rejects foreign origins)."""
    if _env("ACE_DEVICE_SERIAL") or _env("ACE_CDP_BROWSER_WS"):
        return False
    # If the active context targets an Android app, don't auto-launch local Chrome
    if _app_package() and _app_package() != "com.studentsyncsa.studentsyncsa":
        pass  # let device discovery handle it
    elif _app_package() == "com.studentsyncsa.studentsyncsa" and not _env("ACE_DEVICE_PACKAGE"):
        # Backward compat: old StudentSyncSA default still tries local Chrome
        pass
    port = 9230
    for host in ("127.0.0.1", "[::1]"):
        try:
            urllib.request.urlopen(f"http://{host}:{port}/json/version", timeout=1.5)
            return True  # already up
        except Exception:
            pass
    candidate = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(candidate):
        candidate = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(candidate):
            return False
    profile = r"C:\Users\chris\AppData\Local\Temp\ace_cdp_browser"
    os.makedirs(profile, exist_ok=True)
    logf = open(r"C:\Users\chris\AppData\Local\Temp\ace_cdp.log", "a")
    try:
        subprocess.Popen([candidate, "--headless=new", "--disable-gpu",
                          f"--remote-debugging-port={port}", "--remote-allow-origins=*",
                          "--no-first-run", f"--user-data-dir={profile}",
                          "data:text/html,<script>console.log('ACE browser ready')</script>"],
                         stdout=logf, stderr=subprocess.STDOUT,
                         creationflags=subprocess.DETACHED_PROCESS | _NO_WINDOW)
        for _ in range(8):
            time.sleep(0.5)
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
                return True
            except Exception:
                continue
    except Exception:
        return False
    return False


def _discover_target():
    # 1) explicit ws URL override
    ws = _env("ACE_CDP_BROWSER_WS")
    if ws:
        return {"webSocketDebugUrl": ws, "url": "", "title": "(override)"}
    # 1a) Android app WebView is the PRIMARY target for ACEsi (the ITS OAP form
    #      lives there). Try it FIRST so a local headless Chrome on a scanned
    #      port can never shadow the phone's WebView.
    tgt = _discover_device_webview()
    if tgt:
        return tgt
    # 1b) auto-launch a local headless Chrome (with --remote-allow-origins=*) if none
    #      is already serving on the devtools port. Skipped when the user explicitly
    #      targets a device (ACE_DEVICE_SERIAL set) so device WebViews stay inspectable.
    _ensure_local_browser()
    # 2) local Chrome devtools (desktop) on scanned ports
    return _discover_local_target()


def _discover_local_target(attempts=4, delay=1.0):
    """Scan the local devtools ports for a usable target, retrying briefly.

    Chrome can start accepting connections on the debugging port one or two
    seconds BEFORE its page target appears in /json/list, so an empty or
    unusable target list is retried instead of being reported as 'no browser'.
    """
    ports = []
    try:
        pref = _env("ACE_CDP_PORT")
        if pref:
            ports.append(int(pref))
    except Exception:
        pass
    # The preferred port must actually be scanned. The old loop built the list
    # with the pref first and then guarded on `if port in SCAN_PORTS`, so any
    # ACE_CDP_PORT outside the built-in scan list was silently never queried.
    for p in SCAN_PORTS:
        if p not in ports:
            ports.append(p)
    for attempt in range(attempts):
        for port in ports:
            targets = _list_targets(port)
            if targets:
                sel = _select_target(targets)
                if sel:
                    return sel
        if attempt < attempts - 1:
            time.sleep(delay)
    return None


def _discover_device_webview():
    """Try to reach the Android app's WebView devtools socket via adb forward.
    Returns a target dict or None. Uses the abstract-socket localabstract: form
    which Android WebView requires."""
    pid = _app_pid()
    names = _discover_socket_names()
    # No app process AND no devtools sockets means there is nothing to forward
    # to. Without this short-circuit the adb-forward probing below burns ~60s
    # timing out on ports with nothing behind them, while a local Chrome on the
    # scan list is reachable in ~0.01s. It also used to build a bogus
    # 'webview_devtools_remote_None' candidate when the pid was missing.
    if not pid and not names:
        return None
    candidates = []
    if pid:
        candidates.append("webview_devtools_remote_%s" % pid)
    candidates += ["webview_devtools_remote_0", "chrome_devtools_remote"]
    candidates += names
    host_port = DEFAULT_FORWARD_PORT
    for name in candidates:
        if _adb_forward(name, host_port):
            t = _list_targets(host_port)
            if t:
                return _select_target(t)
    return None


class CdpSession:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self._lock = threading.Lock()
        self._next_id = [0]
        self._responses = {}
        self._cond = threading.Condition()
        self.console_logs = []
        self.network_reqs = {}
        self._running = True
        self._dead = False

    def _send(self, method, params=None):
        with self._lock:
            self._next_id[0] += 1
            mid = self._next_id[0]
            msg = {"id": mid, "method": method}
            if params:
                msg["params"] = params
            self.ws.send(json.dumps(msg))
            return mid

    def _wait(self, mid, timeout=8):
        with self._cond:
            end = time.time() + timeout
            while time.time() < end:
                if mid in self._responses:
                    return self._responses.pop(mid)
                self._cond.wait(timeout=0.5)
            return {"error": "timeout waiting for CDP response (id=%d)" % mid}

    def _recv_loop(self):
        try:
            while self._running:
                frame = self.ws.recv()
                if frame is None:
                    break
                try:
                    msg = json.loads(frame)
                except Exception:
                    continue
                if "id" in msg and msg["id"] is not None:
                    with self._cond:
                        self._responses[msg["id"]] = msg
                        self._cond.notify_all()
                elif "method" in msg:
                    self._on_event(msg["method"], msg.get("params") or {})
        except Exception:
            pass
        finally:
            self._dead = True
            with self._cond:
                self._responses[-1] = {"error": "CDP session closed by remote"}
                self._cond.notify_all()

    def _on_event(self, method, params):
        if method == "Runtime.consoleAPICalled":
            args = params.get("args", [])
            text = " ".join(_json_val(a) for a in args)
            self.console_logs.append({"level": params.get("level"),
                                      "ts": params.get("timestamp"), "text": text})
            if len(self.console_logs) > 2000:
                self.console_logs = self.console_logs[-2000:]
        elif method in ("Network.requestWillBeSent",):
            rid = params.get("requestId")
            self.network_reqs[rid] = {"requestId": rid,
                                       "url": params.get("request", {}).get("url"),
                                       "method": params.get("request", {}).get("method"),
                                       "type": params.get("type"),
                                       "ts": params.get("timestamp")}
        elif method == "Network.responseReceived":
            rid = params.get("requestId")
            if rid in self.network_reqs:
                self.network_reqs[rid]["status"] = params.get("response", {}).get("status")
                self.network_reqs[rid]["mimeType"] = params.get("response", {}).get("mimeType")

    def connect(self):
        # suppress_origin=True: the Android WebView devtools server rejects the
        # WebSocket handshake unless the Origin header matches its allow-list,
        # and it has no --remote-allow-origins flag. Omitting Origin bypasses it.
        self.ws = websocket.create_connection(self.ws_url, timeout=10,
                                              suppress_origin=True)
        t = threading.Thread(target=self._recv_loop, daemon=True)
        t.start()
        for m in ("Runtime.enable", "Log.enable", "Network.enable", "Page.enable", "DOM.enable"):
            self._wait(self._send(m), timeout=6)
        # give event buffers a moment to warm up
        time.sleep(0.4)
        return True


def _json_val(a):
    if not isinstance(a, dict):
        return str(a)
    v = a.get("value")
    if "value" in a:
        return json.dumps(v) if not isinstance(v, str) else v
    return a.get("description", a.get("value", ""))


def _get_session(force=False):
    global _session, _LAST_CONNECT_ERROR
    _LAST_CONNECT_ERROR = ""
    with _session_lock:
        if _session is not None and not force and not getattr(_session, "_dead", False):
            return _session
        if _session is not None:
            try:
                _session.ws.close()
            except Exception:
                pass
            _session = None
        tgt = _discover_target()
        if not tgt:
            return None
        ws_url = tgt["webSocketDebuggerUrl"]
        sess = CdpSession(ws_url)
        try:
            sess.connect()
        except Exception as e:
            # Record WHY so a failed connect is diagnosable instead of always
            # surfacing the same generic "could not connect to any CDP target".
            # NOTE: `global _LAST_CONNECT_ERROR` above is required, otherwise this
            # assignment creates a function-local and connect_cmd() never sees it.
            _LAST_CONNECT_ERROR = "%s: %s" % (type(e).__name__, e)
            print("[cdp] connect to %s failed - %s" % (ws_url, _LAST_CONNECT_ERROR),
                  flush=True)
            return None
        _session = sess
        return _session


def get_console_logs():
    s = _get_session()
    if not s:
        return False, "no reachable CDP target (start the ITS WebView / Chrome, or set ACE_CDP_BROWSER_WS)"
    with _lock:
        logs = list(s.console_logs)
    if not logs:
        return True, "(no console events since connect — call evaluate_js('console.log(...)') first to seed one)"
    lines = ["%s [%s] %s" % (round(l.get("ts", 0), 1), l.get("level"), l.get("text")) for l in logs]
    return True, "\n".join(lines[-80:])


def get_network_requests():
    s = _get_session()
    if not s:
        return False, "no reachable CDP target"
    with _lock:
        reqs = list(s.network_reqs.values())
    if not reqs:
        return True, "(no network requests observed since connect)"
    lines = []
    for r in reqs[-80:]:
        lines.append("%-7s %s %s %s" % (r.get("type"), r.get("method"), (r.get("url") or "")[:70], r.get("status")))
    return True, "\n".join(lines)


def _unwrap_js_value(val):
    """Decode a JS value that is itself a JSON string.

    Page scripts usually report structured data via JSON.stringify(), so CDP
    hands back a *string* that already contains JSON. Running json.dumps() on
    it double-encodes: an array of links comes back as one quoted, escaped
    blob (which is why a 12-link list printed one character per line). Decode
    once here so callers can pretty-print the real structure.
    """
    if isinstance(val, str):
        s = val.strip()
        if len(s) > 1 and s[0] in "[{":
            try:
                return json.loads(s)
            except Exception:
                return val
    return val


def _format_js_value(val, indent=None):
    """Render a JS return value for a model/tool caller.

    Plain strings are passed through unquoted (a model asking for a URL should
    get the URL, not a JSON string literal); real JSON structures are dumped.
    """
    v = _unwrap_js_value(val)
    if isinstance(v, str):
        return v
    return json.dumps(v, indent=indent)


def get_dom_state():
    s = _get_session()
    if not s:
        return False, "no reachable CDP target"
    mid = s._send("Runtime.evaluate", {"expression":
        "JSON.stringify({title:document.title, url:location.href, "
        "html: document.documentElement.outerHTML.slice(0,3000)})"})
    resp = s._wait(mid, timeout=8)
    try:
        val = resp["result"]["result"]["value"]
        return True, _format_js_value(val, indent=2)[:3000]
    except Exception:
        return False, "evaluate failed: %s" % json.dumps(resp)[:400]


def evaluate_js(expr):
    if not expr:
        return False, "usage: evaluate_js <expression>"
    s = _get_session()
    if not s:
        return False, "no reachable CDP target"
    mid = s._send("Runtime.evaluate", {"expression": expr})
    resp = s._wait(mid, timeout=10)
    try:
        result = resp.get("result") or {}
        # A thrown JS error is the normal failure mode while debugging a page,
        # so report it directly instead of an opaque "evaluate failed".
        exc = result.get("exceptionDetails")
        if exc:
            detail = exc.get("exception") or {}
            return False, ("JS error: %s" % (detail.get("description")
                                            or detail.get("value")
                                            or json.dumps(exc)[:300]))
        r = result["result"]
        val = r.get("value")
        if "value" in r:
            return True, _format_js_value(val)
        return True, r.get("description", str(r))
    except Exception:
        return False, "evaluate failed: %s" % json.dumps(resp)[:500]


def navigate_url(url, timeout=25):
    """Navigate the attached page via CDP Page.navigate and wait for load.

    Preferred over `evaluate_js("location.href=...")`: it uses the real browser
    navigation path (so the Network panel records a proper Document request),
    returns a loaderId, and cannot be defeated by a page that overwrites
    location. Waits for document.readyState == 'complete' before returning, so
    cdp_dom_state / cdp_network_requests see the new page.
    """
    if not url:
        return False, "usage: navigate_url <url>"
    s = _get_session()
    if not s:
        return False, "no reachable CDP target (start the ITS WebView / Chrome, or set ACE_CDP_BROWSER_WS)"
    if "://" not in url:
        url = "https://" + url
    mid = s._send("Page.navigate", {"url": url})
    resp = s._wait(mid, timeout=15) or {}
    err = resp.get("error")
    if err:
        return False, "navigate to %s failed: %s" % (url, json.dumps(err)[:300])
    res = resp.get("result") or {}
    if res.get("errorText"):
        return False, "navigate to %s failed: %s" % (url, res["errorText"])

    deadline = time.time() + max(3, timeout)
    state, href = "", ""
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            r = s._wait(s._send("Runtime.evaluate", {"expression":
                       "document.readyState + '|' + location.href"}), timeout=6)
            raw = (r.get("result") or {}).get("result", {}).get("value", "")
            state, _, href = str(raw).partition("|")
        except Exception:
            state, href = "", ""
        # Require the new document, not a leftover readyState from the old page.
        if state.strip() == "complete" and _same_page(href, url):
            break

    loader = res.get("loaderId", "?")
    if state.strip() != "complete":
        return True, ("navigated to %s (loaderId=%s) but the page had not finished "
                      "loading after %ss (readyState=%s, href=%s)"
                      % (url, loader, timeout, state or "?", href or "?"))
    if not _same_page(href, url):
        return True, ("navigated to %s (loaderId=%s) but the browser ended up at %s "
                      "- the site may have redirected" % (url, loader, href or "?"))
    return True, "navigated to %s (loaderId=%s, readyState=complete)" % (url, loader)


def _same_page(href, url):
    """Loose href comparison: ignore scheme case, 'www.', trailing slash, fragment."""
    def norm(u):
        u = (u or "").strip()
        u = re.sub(r"^https?://", "", u, flags=re.I)
        u = re.sub(r"^www\.", "", u, flags=re.I)
        u = u.split("#")[0].rstrip("/")
        return u.lower()
    a, b = norm(href), norm(url)
    return bool(a) and bool(b) and (a == b or a.startswith(b) or b.startswith(a))


def connect_cmd():
    s = _get_session(force=True)
    if not s:
        detail = (" Last WebSocket error: %s" % _LAST_CONNECT_ERROR
                  if _LAST_CONNECT_ERROR else "")
        return False, ("could not connect to any CDP target (ITS WebView not open / "
                       "not debuggable, or set ACE_CDP_BROWSER_WS)." + detail)
    tgt = s.ws_url
    return True, "connected to CDP target %s" % tgt


def status():
    s = _session
    return {"connected": s is not None,
            "ws_url": s.ws_url if s else "",
            "console_events": len(s.console_logs) if s else 0,
            "network_events": len(s.network_reqs) if s else 0}
