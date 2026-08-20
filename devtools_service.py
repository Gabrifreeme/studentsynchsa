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

import os, sys, json, time, threading, subprocess
import urllib.request
import websocket

APP_PACKAGE = "com.studentsyncsa.studentsyncsa"
DEFAULT_FORWARD_PORT = 9229
SCAN_PORTS = [9230, 9222, 9229, 9223, 9225]

_lock = threading.RLock()
_session = None
_session_lock = threading.Lock()


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
    out = _adb("shell", "pidof " + APP_PACKAGE)
    tok = (out or "").split()
    return tok[0] if tok else None


def _select_target(targets):
    frag = _env("ACE_CDP_URL_FRAGMENT", "").lower()
    pages = [t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
    if frag:
        for t in pages:
            u = ((t.get("url") or "") + " " + (t.get("title") or "")).lower()
            if frag in u:
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
    pref = _env("ACE_CDP_PORT")
    ports = []
    try:
        if pref:
            ports.append(int(pref))
    except Exception:
        pass
    ports += SCAN_PORTS
    for port in ports:
        if port in SCAN_PORTS:
            t = _list_targets(port)
            if t:
                return _select_target(t)
    return None


def _discover_device_webview():
    """Try to reach the Android app's WebView devtools socket via adb forward.
    Returns a target dict or None. Uses the abstract-socket localabstract: form
    which Android WebView requires."""
    pid = _app_pid()
    candidates = [f"webview_devtools_remote_{pid}", "webview_devtools_remote_0",
                  "chrome_devtools_remote"]
    candidates += _discover_socket_names()
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
    global _session
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
        return True, json.dumps(val, indent=2)[:3000]
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
        r = resp["result"]["result"]
        val = r.get("value")
        if "value" in r:
            return True, json.dumps(val)
        return True, r.get("description", str(r))
    except Exception:
        return False, "evaluate failed: %s" % json.dumps(resp)[:500]


def connect_cmd():
    s = _get_session(force=True)
    if not s:
        return False, "could not connect to any CDP target (ITS WebView not open / not debuggable, or set ACE_CDP_BROWSER_WS)"
    tgt = s.ws_url
    return True, "connected to CDP target %s" % tgt


def status():
    s = _session
    return {"connected": s is not None,
            "ws_url": s.ws_url if s else "",
            "console_events": len(s.console_logs) if s else 0,
            "network_events": len(s.network_reqs) if s else 0}
