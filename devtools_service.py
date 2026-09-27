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
        # requestId -> start time, for requests that have not finished yet.
        # A dict (not a counter) so a redirect reusing a requestId, a duplicate
        # event, or a lost loadingFinished cannot corrupt the count.
        self._inflight = {}
        # Last time ANY network event arrived; the idle watermark.
        self._last_net_activity = 0.0
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
            req = params.get("request", {})
            # A redirect re-uses the SAME requestId and never emits
            # loadingFinished for the original hop, so the new request must not
            # overwrite the old record. Without this, a login POST that answers
            # 302 -> /secure vanished completely: only the final GET survived.
            redirect = params.get("redirectResponse")
            if redirect is not None and rid in self.network_reqs:
                prev = self.network_reqs[rid]
                prev["status"] = redirect.get("status")
                prev["mimeType"] = redirect.get("mimeType")
                prev["response_headers"] = redirect.get("headers") or {}
                prev["state"] = "done"
                prev["redirected_to"] = req.get("url")
                self._rekey(prev)
                self._inflight.pop(rid, None)
            self.network_reqs[rid] = {"requestId": rid,
                                       "cdp_id": rid,
                                       "url": req.get("url"),
                                       "method": req.get("method"),
                                       "type": params.get("type"),
                                       "ts": params.get("timestamp"),
                                       "state": "pending",
                                       "postData": (req.get("postData") or "")[:2000] or None,
                                       "response_headers": None}
            # Only count it as in-flight once (see the redirect case above).
            self._inflight[rid] = time.time()
            self._last_net_activity = time.time()

        elif method == "Network.responseReceived":
            rid = params.get("requestId")
            resp = params.get("response", {})
            if rid in self.network_reqs:
                self.network_reqs[rid]["status"] = resp.get("status")
                self.network_reqs[rid]["mimeType"] = resp.get("mimeType")
                self.network_reqs[rid]["protocol"] = resp.get("protocol")
                self.network_reqs[rid]["remoteIPAddress"] = resp.get("remoteIPAddress")
                self.network_reqs[rid]["fromDiskCache"] = resp.get("fromDiskCache")
                # Needed to tell a real 4xx/5xx page from a transport failure, and
                # to see where a redirect was sent.
                self.network_reqs[rid]["response_headers"] = resp.get("headers") or {}
        elif method in ("Network.loadingFinished", "Network.loadingFailed"):
            rid = params.get("requestId")
            self._inflight.pop(rid, None)
            self._last_net_activity = time.time()
            rec = self.network_reqs.get(rid)
            if rec is not None:
                rec["state"] = "done"
                if method == "Network.loadingFailed":
                    # Distinguish "failed before any response" from "still in
                    # flight" - both used to render as a bare status of None.
                    rec["state"] = "failed"
                    rec["errorText"] = params.get("errorText")
                    rec["canceled"] = params.get("canceled")
        elif method == "Network.requestWillBeSentExtraInfo":
            pass

    def _rekey(self, rec):
        """Move an already-captured hop to its own key so the reused requestId
        is free for the next hop. Both hops stay visible to callers, and
        requestId/cdp_id keep pointing at the real CDP id so
        Network.getResponseBody can still be called for this hop."""
        old = rec.get("requestId")
        n = 1
        while True:
            k = "%s#hop%d" % (old, n)
            if k not in self.network_reqs:
                if old in self.network_reqs and self.network_reqs[old] is rec:
                    del self.network_reqs[old]
                self.network_reqs[k] = rec
                return
            n += 1

    def network_idle(self, idle_ms=500):
        """True when no request is in flight AND nothing has hit the wire for
        idle_ms. Polling pages therefore never look idle, and the caller's
        timeout is what bounds the wait."""
        with self._lock:
            busy = len(self._inflight)
            last = self._last_net_activity
        if busy:
            return False, "%d request(s) still in flight" % busy
        quiet = (time.time() - last) * 1000.0
        if quiet < float(idle_ms):
            return False, "last network activity was %dms ago (need %dms)" % (
                int(quiet), int(idle_ms))
        return True, "no requests in flight for %dms" % int(idle_ms)

    def reset_network_tracking(self):
        """Drop in-flight state. Called before a navigation: requests belonging
        to the page being replaced will never emit loadingFinished, so leaving
        them counted would make network_idle() unreachable forever."""
        with self._lock:
            self._inflight.clear()
            self._last_net_activity = time.time()

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
        # Carry the request history across a reconnect. A form submit that
        # redirects tears down the WebSocket, the session is rebuilt, and the
        # fresh one starts with an empty log - so the POST that caused the
        # navigation is the one request that goes missing. Everything captured
        # so far is a historical fact, so keep it and mark where it came from.
        _carry = []
        if _session is not None:
            try:
                with _lock:
                    _carry = [dict(r) for r in _session.network_reqs.values()]
            except Exception:
                _carry = []
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
        if _carry:
            for _r in _carry:
                _key = _r.get("requestId") or _r.get("cdp_id") or ("carried-%d" % id(_r))
                if _key in sess.network_reqs:
                    _key = "%s#carried" % _key
                _r["carried_over"] = True
                sess.network_reqs[_key] = _r
            print("[cdp] carried %d request(s) across a reconnect" % len(_carry),
                  flush=True)
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


_DIAG_HEADERS = ("content-type", "content-length", "location", "server",
                 "cache-control", "strict-transport-security", "date")


def _status_pred(filter_status):
    """Build a status matcher from 404, "404", "4xx", "404,500" or [404, "5xx"].

    Returns None for no filter. Accepts the class form so a model can ask for
    "any 4xx" without pulling every request into its context first.
    """
    if filter_status is None or filter_status == "":
        return None
    if isinstance(filter_status, (list, tuple, set)):
        parts = list(filter_status)
    else:
        parts = str(filter_status).replace(" ", "").split(",")
    exact, classes = set(), []
    for p in parts:
        if p == "":
            continue
        p = str(p).strip()
        if re.fullmatch(r"[1-5]?[0-9]xx", p, re.I):
            classes.append(int(p[0]))
        else:
            try:
                exact.add(int(p))
            except ValueError:
                return None
    if not exact and not classes:
        return None

    def pred(st):
        if st is None:
            return False
        return st in exact or (int(st) // 100) in classes
    return pred


def _fmt_headers(headers):
    """Compact diagnostic header summary.

    Full headers are retained on the record; rendering all of them for a page
    with 500 requests would blow the model's token budget, which is the reason
    the filter parameters exist in the first place.
    """
    if not headers:
        return ""
    low = {str(k).lower(): v for k, v in headers.items()}
    keep = [h for h in _DIAG_HEADERS if h in low]
    keep += sorted(k for k in low if k.startswith("x-") and k not in keep)
    out = []
    for h in keep[:10]:
        v = low[h]
        if isinstance(v, list):
            v = ", ".join(str(x) for x in v)
        out.append("%s=%s" % (h, str(v)[:70]))
    return " | ".join(out)


def request_ids():
    """Keys currently in the request log. Snapshot this before an action, then
    pass it to find_new_requests() to see only what that action caused."""
    s = _get_session()
    if not s:
        return set()
    with _lock:
        return set(s.network_reqs.keys())


def find_new_requests(before=None, methods=("POST",), timeout=6.0, interval=0.3,
                      url_contains=None, require_done=False):
    """Wait for a request that appeared after `before` and matches `methods`.

    get_network_requests() returns a formatted string, which is no use for
    deciding "did the click I just made cause a POST?". This returns the records
    themselves, so the caller can read the status and Location directly and
    report the answer without asking a model to go and look.

    require_done waits for the response to arrive, not just the request. A record
    exists from RequestWillBeSent, with status still None, so returning early
    would report a request as "pending" when the caller is trying to state its
    final status. Records that fail outright count as done.
    """
    before = set(before or ())
    want = {str(m).upper() for m in methods} if methods else None
    needle = str(url_contains).lower() if url_contains else None
    deadline = time.time() + max(0.0, float(timeout))
    while True:
        s = _get_session()
        if s:
            with _lock:
                fresh = [r for k, r in s.network_reqs.items() if k not in before]
            hit = [r for r in fresh
                   if (want is None or str(r.get("method") or "").upper() in want)
                   and (needle is None or needle in (r.get("url") or "").lower())]
            if require_done:
                done = [r for r in hit
                        if r.get("status") is not None or r.get("state") == "failed"]
                if done:
                    return done
            elif hit:
                return hit
        if time.time() >= deadline:
            return []
        time.sleep(max(0.05, float(interval)))


def get_network_requests(filter_status=None, filter_url=None, limit=100):
    s = _get_session()
    if not s:
        return False, "no reachable CDP target"
    with _lock:
        reqs = list(s.network_reqs.values())
    try:
        limit = max(1, int(limit))
    except Exception:
        limit = 100

    pred = _status_pred(filter_status)
    if filter_url:
        needle = str(filter_url).lower()
        reqs = [r for r in reqs if needle in (r.get("url") or "").lower()]
    if pred:
        reqs = [r for r in reqs if pred(r.get("status"))]
    if not reqs:
        what = []
        if filter_status is not None:
            what.append("status=%s" % filter_status)
        if filter_url:
            what.append("url~%s" % filter_url)
        return True, ("(no request matched %s — %d request(s) observed since connect)"
                      % (", ".join(what) or "anything", len(s.network_reqs)))

    total = len(reqs)
    shown = reqs[-limit:]
    lines = []
    for r in shown:
        st = r.get("status")
        state = r.get("state") or ("done" if st is not None else "pending")
        # A bare "None" was ambiguous between "still loading" and "failed";
        # name the state instead.
        shown_status = st if st is not None else (
            "failed:%s" % r.get("errorText") if state == "failed" else "pending")
        line = "%-10s %-6s %-7s %s" % (r.get("type"), r.get("method"),
                                        shown_status, (r.get("url") or "")[:90])
        hdr = _fmt_headers(r.get("response_headers"))
        if hdr:
            line += "\n           headers: %s" % hdr
        lines.append(line)
    note = ""
    if total > len(shown):
        note = "\n(showing the most recent %d of %d matches; raise `limit` to see more)" % (
            len(shown), total)
    return True, "\n".join(lines) + note


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


def get_response_body(url_contains=None, filter_status=None, max_chars=4000):
    """Fetch the body of a captured response via Network.getResponseBody.

    Chrome only retains a body while the response is still available, so this
    legitimately fails for requests whose body was evicted (after a navigation,
    or for large streamed responses). Say so plainly instead of returning "".
    """
    s = _get_session()
    if not s:
        return False, "no reachable CDP target"
    with _lock:
        reqs = [r for r in s.network_reqs.values()
                if r.get("state") == "done" and r.get("status") is not None]
    if url_contains:
        needle = str(url_contains).lower()
        reqs = [r for r in reqs if needle in (r.get("url") or "").lower()]
    pred = _status_pred(filter_status)
    if pred:
        reqs = [r for r in reqs if pred(r.get("status"))]
    if not reqs:
        return False, ("no completed request matched (url_contains=%r, filter_status=%r). "
                       "Bodies must be read before the page navigates away."
                       % (url_contains, filter_status))
    rec = reqs[-1]
    cdp_id = rec.get("cdp_id") or rec.get("requestId")
    mid = s._send("Network.getResponseBody", {"requestId": cdp_id})
    resp = s._wait(mid, timeout=8) or {}
    if resp.get("error"):
        return False, ("could not read the body of %s %s (status %s): %s - Chrome only "
                       "keeps a response body until it is evicted, so read it right "
                       "after the request rather than after navigating."
                       % (rec.get("method"), rec.get("url"), rec.get("status"),
                          json.dumps(resp["error"])[:200]))
    result = resp.get("result") or {}
    body = result.get("body") or ""
    if result.get("base64Encoded"):
        try:
            import base64
            body = base64.b64decode(body).decode("utf-8", "replace")
        except Exception:
            return False, "response body was base64 and could not be decoded"
    shown = body[:max_chars]
    return True, ("%s %s (status %s), %d byte(s):\n%s%s"
                  % (rec.get("method"), rec.get("url"), rec.get("status"),
                     len(body), shown, "\n... (truncated)" if len(body) > max_chars else ""))


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


def navigate_url(url, wait=True, wait_for="load", timeout=30, idle_ms=500):
    """Navigate the attached page via CDP Page.navigate.

    Preferred over `evaluate_js("location.href=...")`: it uses the real browser
    navigation path (so the Network panel records a proper Document request),
    returns a loaderId, and cannot be defeated by a page that overwrites
    location.

    wait_for:
      "load"         -> return once document.readyState == 'complete'
      "network_idle" -> additionally wait until no request is in flight and
                        nothing has hit the wire for idle_ms. Use this when the
                        page has background polling (analytics, keep-alive, ad
                        beacons, feature flags) and the request you care about
                        is a late XHR: under "load" readyState fires first and
                        the late request would be missed entirely.
    wait=False -> fire Page.navigate and return immediately, without waiting.
    timeout caps the wait, so a page that polls forever cannot hang.
    """
    if not url:
        return False, "usage: navigate_url <url>"
    wait_for = (wait_for or "load").strip().lower()
    if wait_for not in ("load", "network_idle"):
        return False, 'wait_for must be "load" or "network_idle", got %r' % wait_for
    s = _get_session()
    if not s:
        return False, "no reachable CDP target (start the ITS WebView / Chrome, or set ACE_CDP_BROWSER_WS)"
    if "://" not in url:
        url = "https://" + url
    # Requests belonging to the page being replaced will never emit
    # loadingFinished, so clear them before navigating or network_idle() can
    # never be reached.
    s.reset_network_tracking()
    mid = s._send("Page.navigate", {"url": url})
    resp = s._wait(mid, timeout=15) or {}
    err = resp.get("error")
    if err:
        return False, "navigate to %s failed: %s" % (url, json.dumps(err)[:300])
    res = resp.get("result") or {}
    if res.get("errorText"):
        return False, "navigate to %s failed: %s" % (url, res["errorText"])
    loader = res.get("loaderId", "?")
    if not wait:
        return True, "navigating to %s (loaderId=%s, not waiting)" % (url, loader)

    try:
        timeout = max(3, float(timeout))
    except Exception:
        timeout = 30.0
    try:
        idle_ms = max(50, float(idle_ms))
    except Exception:
        idle_ms = 500.0

    deadline = time.time() + timeout
    state, href, why = "", "", ""
    while True:
        time.sleep(0.4)
        try:
            r = s._wait(s._send("Runtime.evaluate", {"expression":
                       "document.readyState + '|' + location.href"}), timeout=6)
            raw = (r.get("result") or {}).get("result", {}).get("value", "")
            state, _, href = str(raw).partition("|")
        except Exception:
            state, href = "", ""
        state = state.strip()
        loaded = state == "complete" and _same_page(href, url)
        if loaded:
            if wait_for == "load":
                break
            ok_idle, why = s.network_idle(idle_ms)
            if ok_idle:
                break
        elif wait_for == "network_idle" and not state:
            # evaluate failed (execution context swapped mid-navigation); fall
            # back to the network signal alone rather than spinning.
            ok_idle, why = s.network_idle(idle_ms)
            if ok_idle:
                break
        if time.time() >= deadline:
            break

    if state != "complete":
        return True, ("navigated to %s (loaderId=%s) but the page had not finished "
                      "loading after %ss (readyState=%s, href=%s)"
                      % (url, loader, timeout, state or "?", href or "?"))
    if not _same_page(href, url):
        return True, ("navigated to %s (loaderId=%s) but the browser ended up at %s "
                      "- the site may have redirected" % (url, loader, href or "?"))
    if wait_for == "load":
        return True, "navigated to %s (loaderId=%s, readyState=complete)" % (url, loader)
    ok_idle, why = s.network_idle(idle_ms)
    if ok_idle:
        return True, ("navigated to %s (loaderId=%s, readyState=complete, %s)"
                      % (url, loader, why))
    return True, ("navigated to %s (loaderId=%s, readyState=complete) but the network "
                  "never went idle within %ss (%s) - background requests are still "
                  "in flight, so later requests may not be captured yet"
                  % (url, loader, timeout, why))


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
