# Oracle ITS Portal — Battle Plan

**Target:** `https://univenierp01.univen.ac.za/pls/prodi41/` (UNIVEN online application wizard)
**App:** LipSyncStudent (Flutter, Android tablet `R52N518ESBE`, SM-T515, Android 11, WebView 155.0.8059.43)
**Written:** 26 Oct 2026, night before execution
**Status:** PLAN ONLY — no code has been changed. Everything below is a proposal.

---

## 0. Read this first (60 seconds)

The thing we have been calling a "WAF" is **not a WAF**.

There is no Cloudflare, no Akamai, no mod_security, no User-Agent block. We proved that with a
full UA/Referer matrix (section 1.4). What we actually have is:

1. **A session guard.** The portal only serves the real wizard if a server-side session exists
   and the `sessid` cookie is presented. Without it, `/gen.gw1pkg.gw1view` returns a 4,832-byte
   stub that **deletes `sessid` and redirects to `/itsdocs/wizard_access.html`** — the
   "Access Denied — A serious security exception…" page.
2. **A broken entry point in our app.** Nothing in `lib/` ever loads the one URL that creates the
   session (`gen.gw1pkg.gw1startup?x_processcode=ITS_OAP`). Worse, the routed screen
   (`UniversityWebViewScreen`) **refuses to load any ITS URL at all** and bounces to
   `https://www.univen.ac.za/apply/`.
3. **A URL-truncation 404 species** that is separate from the session problem: procedure names
   arriving as `gw1v` / `gw1p` / `gw1` return a genuine HTTP **404**.

So there are two bugs wearing one mask, and the mask is off now.

**The single highest-value action tomorrow is not a header trick. It is: load
`gw1startup?x_processcode=ITS_OAP` top-level, let it set `sessid`, and let *it* redirect to
`gw1view` — and stop the app from hijacking that navigation.**

---

## 1. What the "WAF" actually is (evidence, not guesswork)

All of the following was measured from this PC against the live server on 25–26 Oct 2026.

### 1.1 The working handshake

```
GET https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP
→ 200, 3,096 bytes, Server: Oracle-HTTP-Server-12c
   body contains a JS shim that runs  setCookie('sessid', '<32 hex>', '; PATH=/')
   then  location.replace('gen.gw1pkg.gw1view')
```

Taking that `sessid` value and re-requesting the view **with it** changes everything:

```
GET .../gen.gw1pkg.gw1view      (no cookie) → 200,  4,832 bytes → "cannot find detail" → Access Denied
GET .../gen.gw1pkg.gw1view      (sessid)    → 200, 15,286 bytes → REAL wizard page
```

The real page is `<title>Comprehensive Web Application Process</title>`, contains
`<div id="ITS_OAP" class="process">`, form `frmOne`, and these live field IDs:

```
oapAcceptPopi_ChkBx   oapNotAcceptPopi_ChkBx   oapReturnIDNo
oapReturnPPNo        oapOldNew                oapNextBtn1
```

That is the POPI-consent / returning-applicant start page. **This is what a successful load
looks like.** It is our acceptance test (section 7).

### 1.2 Why the failure page is a trap

The 4,832-byte stub is not an error page — it is a **deliberate session killer**:

```js
function redirectme() {
  var thisCookie = document.cookie.split(";");
  for (i=0; i<thisCookie.length; i++) {
    cookieName = thisCookie[i].split("=")[0];
    if (cookieName == " sessid") { document.cookie = cookieName + "=;path=/"; }   // ← deletes it
  }
  parent.location.replace('/itsdocs/wizard_access.html');                          // ← then "Access Denied"
}
```

Consequences:

* If we land on `gw1view` **first**, the page actively destroys any session cookie and sends us
  to the "Access Denied" screen. From there, every retry is poisoned.
* It uses `parent.location` — the wizard was built to live inside a frameset. Loading it
  **top-level** (`parent === self`) sidesteps the whole third-party-cookie class of problems.
* `/itsdocs/wizard_access.html` is a **static HTML file**. It is not a WAF block page. It is
  what the portal *tells you* to look at when your session is missing.

### 1.3 The 404 species (separate bug)

| URL | Result |
|---|---|
| `.../gen.gw1pkg.gw1view` | 200 |
| `.../gen.gw1pkg.gw1startup?x_processcode=ITS_OAP` | 200 |
| `.../gen.gw1pkg.gw1v` | **404** (210 bytes) |
| `.../gen.gw1pkg.gw1p` | **404** (210 bytes) |
| `.../gen.gw1pkg.gw1` | **404** (209 bytes) |
| `.../gen.gw1pkg.gw1view?x_processcode=ITS_OAP` | **404** (213 bytes) |

Two rules fall out of this:

* **Query params are only legal on `gw1startup`.** Adding `x_processcode` to `gw1view` is an
  instant 404. (Commit `0c9ebf6` removed it for exactly this reason — keep it removed.)
* **Truncated procedure names are real 404s**, not a WAF. The `ItsUrl` repair logic is correct
  and must stay.

### 1.4 What we proved does *not* matter

| Variable | Tested values | Result |
|---|---|---|
| User-Agent | desktop Chrome, Android Chrome, Android WebView (`; wv)`), iPhone Safari, `python-requests`, *no UA at all* | **all 200** |
| Referer | `www.univen.ac.za/apply/`, the portal itself, none | **all 200** |
| TLS | `curl` default verification | `ssl_verify_result=0`, valid chain, no `-k` needed |
| ALPN | client offers http/1.1 only | server accepts http/1.1 (no h2) |
| Third-party cookies | server-side irrelevant for a top-level load | n/a |

**Conclusion:** UA spoofing and Referer manipulation were never going to fix this. They are not
the gate. They stay in the plan only as *instrumentation*, not as the fix.

### 1.5 One more confirmed 403

```
GET https://univenierp01.univen.ac.za/        → 403 Forbidden (Apache, 199 bytes)
```

**Never warm up on the portal root.** It is a directory listing that Apache refuses. Any
"warm-up" strategy based on `/` starts from a 403 and looks like a WAF.

---

## 2. What we already tried (and the actual lesson)

| # | Attempt | Where it lives | Outcome | Lesson |
|---|---|---|---|---|
| 1 | **Mobile UA spoof** — HONOR ABR-NX1 / Android 15 Chrome UA | commit `f70c4a7`, later replaced | No effect | UA is not the gate |
| 2 | **Desktop UA spoof** — Windows Chrome 120 | `university_webview_screen.dart:53`, `university_portal_screen.dart:57-59` | No effect; may actively hurt (desktop markup on a touch tablet) | Remove it, test with the default WebView UA |
| 3 | **Third-party cookies** — `setAcceptThirdPartyCookies(controller, true)` | `university_webview_screen.dart:45-48` | No effect | Only matters inside an iframe; we load top-level |
| 4 | **Cookie clearing** — `WebViewCookieManager().clearCookies()` at startup | removed in `f3a21c8` | Made things *worse* | **Never clear cookies**; it races the load and kills the session the portal just created |
| 5 | **Base-URL "warm-up"** — load `https://www.univen.ac.za/apply/` first, then hand off | `university_webview_screen.dart:99-101` + the `onPageStarted` redirect at `:56-69` | Worse than nothing: the redirect *also* catches the portal itself, so the portal can never load | This is the bug, not the fix |
| 6 | **SSL bypass** — `onSslAuthError` + accept-bad-cert | `f70c4a7` (`onSslAuthError`), later removed | No effect; TLS is valid | Keep a *scoped, logging* handler only (Phase 4) |
| 7 | **fetch-hijack POST** — re-POST the wizard form to `gw1proc` via `fetch`, `document.write` the response | commit `39677dd`, later removed | Broke the ITS event model | Do not resurrect |
| 8 | **gw1 URL normalization** — `gw1v→gw1view`, `gw1p→gw1proc`, host typo repair, http→https | `lib/services/its_url_fixer.dart` | Correct and still needed | Keep; extend to `gw1startup` |
| 9 | **Apply-button JS interceptor** — hook submit buttons, resolve relative hrefs | `lib/services/apply_interceptor.dart`, `buildNavigationFixScript()` | Neutral-to-harmful; can turn a POST into a GET | Audit before trusting (Phase 6) |
| 10 | **Direct `gw1view` load** — the current "entry point" | `mock_university_data.dart:63-64`, `university_portal_screen.dart:49-52` | Guaranteed Access Denied | Wrong door. Use `gw1startup` |

---

## 3. Root causes in the current code (P0 — fix these first)

### RC-1 — The routed screen refuses to load the portal at all

`lib/presentation/screens/universities/university_webview_screen.dart`

```dart
// :56-69  onPageStarted
if (url.contains('univenierp01') || url.contains('gw1view') || url.contains('prodi41')) {
  _controller.loadRequest(Uri.parse('https://www.univen.ac.za/apply/'));   // ← bounces the portal
  return;
}

// :99-101  initState
_controller.loadRequest(Uri.parse('https://www.univen.ac.za/apply/'));     // ← ignores widget.url
```

The screen **never uses `widget.url`**. It always opens the university's marketing page, and any
navigation that *does* reach the ITS host is instantly redirected away. The portal cannot load
even in principle. This is the reason every WAF theory has been untestable from inside the app.

### RC-2 — Nothing loads the session-creating URL

```
$ grep -rn "gw1startup" lib/          
lib/presentation/screens/universities/university_detail_screen.dart:425:  url.contains('gw1startup');   ← only a sniff test
```

`gw1startup?x_processcode=ITS_OAP` is referenced **nowhere**. The app has no path to a session.

### RC-3 — The data layer ships the wrong entry URL

`lib/data/datasources/mock_university_data.dart:63-64`

```dart
applicationUrl: 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
```

This is the URL that produces the 4,832-byte stub → Access Denied. Change it to the startup URL
(or, better, let the screen build it and treat the data URL as a fallback).

### RC-4 — The "correct" screen is dead code *and* has the same wrong entry point

`UniversityPortalScreen` (`university_portal_screen.dart`) is never routed — `app_router.dart:110`
and `:151` both construct `UniversityWebViewScreen`. But even if it were routed, it would still fail:

```dart
// :49-52
if (_isUniven) {
  initialUrl = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view';  // ← same trap
}
```

So there is **no working screen in the repo to fall back to.** Both need the entry-point fix.

RC-4 is still the better foundation: it has `onNavigationRequest` normalization, the
`FlutterNavigation`/`FlutterLog` JS channels, `ItsUrl.normalize`, and `_recoverTruncatedPage`.

### RC-5 — Release builds have no `INTERNET` permission

`android/app/src/main/AndroidManifest.xml` declares no `<uses-permission>`. Only
`src/debug/` and `src/profile/` add it. Debug builds work; **release builds cannot open the
network at all.** Add it to `main` before any release build.

### RC-6 — WebView debugging is enabled on the wrong plugin

`lib/main.dart:16` calls `InAppWebViewController.setWebContentsDebuggingEnabled(true)` — that is
the **flutter_inappwebview** API. The ITS screen uses **webview_flutter**, so nothing is enabled
and `chrome://inspect` / CDP cannot attach. The correct call is
`AndroidWebViewController.enableDebugging(true)` (confirmed present in `webview_flutter_android-4.14.1`).

### RC-7 — We are blind to HTTP error codes

The delegates use `onWebResourceError` only. That fires on transport errors, not on a 404/403
response body. `webview_flutter 4.14.1` supports `onHttpError` (`NavigationDelegate`, confirmed in
the installed package) — it is unused. That is why the app has never told us *which* URL 404'd.

### RC-8 — `buildNavigationFixScript` can convert a POST into a GET

`autofill_script.dart:787-795`

```js
el.addEventListener('click', function(e) {
  var href = el.getAttribute('href');
  if (!href) return;
  window.location.assign(resolveUrl(href));   // ← GET, always
}, true);
```

`<input type="submit">` has no `href`, so it escapes — but any anchor-styled ITS button
(`<a class="t-Button">`) is hijacked into a **GET**. On a PL/SQL wizard, a GET where a POST was
expected is indistinguishable from a session violation. This is a plausible secondary cause of
"the page reloads and then Access Denied".

---

## 4. Files to modify

Nothing here is changed yet. Ordered by priority.

| Pri | File | Change | Risk |
|---|---|---|---|
| P0 | `lib/presentation/screens/universities/university_webview_screen.dart` | Stop ignoring `widget.url`; **delete** the `onPageStarted` ITS redirect; remove the forced desktop UA; add `onHttpError` + `onUrlChange` logging; add a debug URL banner | Low |
| P0 | `lib/core/router/app_router.dart` (lines ~104-115, ~146-156) | Route ITS URLs to `UniversityPortalScreen` (or make `UniversityWebViewScreen` the single good screen and delete the other) | Low |
| P0 | `lib/data/datasources/mock_university_data.dart` (~63) | `applicationUrl` → `.../gen.gw1pkg.gw1startup?x_processcode=ITS_OAP` | Low |
| P0 | `lib/presentation/screens/universities/university_portal_screen.dart` (`:47-52`) | Build the startup URL for UNIVEN instead of hardcoding `gw1view`; pass the profile JSON in | Low |
| P0 | `android/app/src/main/AndroidManifest.xml` | `<uses-permission android:name="android.permission.INTERNET"/>` | None |
| P1 | `lib/main.dart` (`:16`) | `AndroidWebViewController.enableDebugging(true)` (keep the inappwebview call if that plugin is retained) | None |
| P1 | `lib/services/its_url_fixer.dart` | Add `isStartupUrl()` / `buildStartupUrl()` helpers; ensure `normalize()` never mangles `gw1startup` | Low |
| P1 | `lib/services/autofill_script.dart` (`:766-826`) | Navfix: never `window.location.assign` a submit control; only rewrite a *truncated* form `action`; never rewrite `gw1proc` | Medium |
| P2 | `lib/services/autofill_script.dart` | Add `oapAcceptPopi_ChkBx`, `oapReturnIDNo`, `oapReturnPPNo`, `oapNextBtn1` to the autofill field map | Low |
| P2 | `lib/presentation/screens/universities/university_portal_screen.dart` | Detect the 4,832-byte stub (`cannot find detail`) and re-run the startup handshake once | Low |
| P3 | new `lib/services/its_webview_controller.dart` (or migrate the screen) | `flutter_inappwebview` implementation with `shouldInterceptRequest`, `onReceivedHttpError`, `onReceivedServerTrustAuthRequest`, custom headers/cookies | **Medium-High** |
| P3 | `pubspec.yaml` | `flutter_inappwebview: ^6.0.0` already declared (resolved 6.1.5) — no change needed unless we drop `webview_flutter` | None |
| — | `apply_interceptor.dart` | **Do not touch tomorrow** unless Phase 6 proves it is implicated | — |

**Do not create** `404-fix-docs/` or `its-url-fix-dashboard/` work — those are Vite scaffolding
templates with no diagnostic content.

---

## 5. Step-by-step plan for tomorrow

Timeboxed. Each phase ends with a **GO / NO-GO** so we never spend six hours on a dead end.

---

### Phase 0 — Establish ground truth (45 min) ← do this before editing anything

**0.1 Prove the network path works outside the app.**

```powershell
adb -s R52N518ESBE shell am start -a android.intent.action.VIEW `
  -d "https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP"
```

Watch what Chrome does. Two outcomes:

* **Chrome reaches the POPI page** → the network and the tablet are fine; the bug is 100% in the
  app. Proceed to Phase 1 with confidence.
* **Chrome also shows Access Denied** → the portal is refusing the tablet's IP/ASN or the
  session is one-shot. Stop and investigate with Phase 0.3 before writing code.

Also open `https://www.univen.ac.za/apply/` in Chrome and follow the real "Apply" link. **Record
the exact URL and whether the wizard appears in an iframe.** If it does, note the iframe `src`
and whether `sessid` survives — that tells us if third-party cookies matter after all.

**0.2 Turn on real WebView debugging.**

`main.dart` → replace the inappwebview call with:

```dart
if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
  await AndroidWebViewController.enableDebugging(true);
}
```

Build, install, open the portal screen, then:

```powershell
adb -s R52N518ESBE shell pidof com.lipsyncstudent.lipsyncstudent
adb -s R52N518ESBE forward tcp:9222 localabstract:webview_devtools_remote_<pid>
```

Open `http://localhost:9222/json` — you should see the page target. If you don't, debugging is
still off and nothing else in this plan is observable.

**0.3 Attach ACEsi's CDP tools.**

In the ACEsi chat:

```
cdp_connect()                                    # attach to the WebView target
cdp_navigate(url="https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP", wait_for="network_idle")
cdp_network_requests(filter_url="prodi41", limit=100)
cdp_console_logs()
cdp_evaluate(expr="document.cookie")
cdp_evaluate(expr="location.href")
cdp_get_response_body(url_contains="gw1view")
```

Record, for every hop: **status, byte count, `Cookie:` sent, `Set-Cookie:` received, final URL.**
The byte count alone tells you which page you are on:

| Bytes | Meaning |
|---|---|
| ~210 | truncated procedure → 404 |
| ~4,832 | session missing → "cannot find detail" → Access Denied |
| ~3,096 | startup shim (good, but transient) |
| ~15,286 | **real wizard / POPI page (success)** |
| ~199 | 403 on `/` — you warmed up on the root, don't |

**NO-GO:** if CDP cannot attach after 45 minutes, skip to Phase 1 and use the on-screen debug
banner + `adb logcat` instead. Do not burn the day on tooling.

---

### Phase 1 — Fix the entry point (1–2 h) ← the actual fix

**1.1** `mock_university_data.dart` → the startup URL.

**1.2** `university_webview_screen.dart` → three surgical deletions/edits:

```dart
// DELETE this entire block from onPageStarted:
//   if (url.contains('univenierp01') || ...) { loadRequest(apply page); return; }

// REPLACE the hardcoded initial load:
_controller.loadRequest(Uri.parse(ItsUrl.normalize(widget.url.isEmpty
    ? _defaultItsUrl
    : widget.url)));

// REMOVE setUserAgent(...) entirely — use the WebView default.
```

**1.3** `university_portal_screen.dart` → for UNIVEN, build the startup URL:

```dart
initialUrl = 'https://univenierp01.univen.ac.za/pls/prodi41/'
             'gen.gw1pkg.gw1startup?x_processcode=ITS_OAP';
```

**1.4** Route to the good screen in `app_router.dart`, and pass the profile JSON through so
autofill has data:

```dart
return UniversityWebViewScreen(
  url: Uri.decodeComponent(rawUrl),
  universityName: Uri.decodeComponent(rawName),
  profileJson: ...,
);
```

**1.5** Add `INTERNET` to the main manifest (do it now, even though debug builds mask it).

**GO:** tap Apply on UNIVEN → you see the POPI consent page with a checkbox, and `cdp_evaluate("location.href")`
has **no** `wizard_access.html` in it.

**If it still fails**, capture the hop chain. The likely culprits, in order:

1. `sessid` never appears in `document.cookie` → cookie policy / the shim was blocked.
2. `sessid` appears but is not sent on the next request → cookie `Path`/`Domain` mismatch.
3. `sessid` is sent but the server returns the 4,832-byte stub → the *server-side* session died
   (the startup request and the view request hit different backends — note the two `Via:` headers:
   `univenperp01` and `univenierp01`).
4. We are back on `gw1view` because something re-navigated there first.

---

### Phase 2 — Make the session survive (1 h)

Once the entry point is right, these are cheap and high-value:

* **Never** call `clearCookies()` anywhere in the ITS flow (already true in
  `university_portal_screen.dart:44-45` — keep that comment).
* Keep `setAcceptThirdPartyCookies(true)` for now; it is harmless and covers the iframe case.
* **Stub detection.** On `onPageFinished`, if `document.body.innerText` contains
  `"Cannot find detail"`, re-run the startup handshake **exactly once** (guard with a bool).
  This self-heals the most common failure without user action.
* **Cookie assertion.** Log `document.cookie` at each hop. If `sessid` is missing after startup,
  log `WebViewCookieManager().getCookies(...)` and compare.
* **Do not** set a `Cookie` header manually with a stale `sessid`. Let the WebView own it.

**GO:** three consecutive cold starts all land on the POPI page. No manual retry.

---

### Phase 3 — Header interception (2–3 h, only if Phase 1/2 are not enough)

This requires `flutter_inappwebview` for **sub-resource** interception (`webview_flutter` cannot
do it). The dependency is already present, so this is a screen rewrite, not a `pubspec` change.

Do it only for the ITS host, and only behind a feature flag.

```dart
InAppWebView(
  initialUrlRequest: URLRequest(
    url: WebUri(startupUrl),
    headers: {
      'Referer': 'https://www.univen.ac.za/apply/',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-ZA,en;q=0.9',
      'Cache-Control': 'no-cache',
    },
  ),
  initialSettings: InAppWebViewSettings(
    useShouldInterceptRequest: true,
    thirdPartyCookiesEnabled: true,
    javaScriptEnabled: true,
    useHybridComposition: true,
    // Do NOT set a custom userAgentString.
  ),
  shouldInterceptRequest: (controller, request) async {
    final u = request.url.toString();
    if (!ItsUrl.isItsHost(u)) return null;
    final fixed = ItsUrl.normalize(u);
    if (fixed != u) {
      // A truncated gw1v/gw1p arrived. Re-issue it corrected, preserving method+body.
      return null; // + log; handle the retry in onReceivedHttpError
    }
    return null; // never synthesise a response
  },
  onReceivedHttpError: (controller, request, response) async {
    debugPrint('ITS HTTP ${response.statusCode} ${request.url}');
  },
  onReceivedServerTrustAuthRequest: (controller, challenge) async {
    // Phase 4 lives here.
    return ServerTrustAuthResponse(action: ServerTrustAuthResponseAction.PROCEED);
  },
)
```

**Rules for this phase:**

* **Do not invent headers the browser would not send.** A hand-rolled `Origin` or a
  mismatched `Sec-Fetch-*` is more likely to trip a server than to help it.
* **Do not rewrite `gw1proc` requests** and do not re-issue POSTs by hand (that was `39677dd`,
  and it failed).
* **Do not fetch-and-`document.write`.** The wizard's JS keeps in-memory state; replacing the
  document loses it.

**GO:** the request log shows one `gw1startup` → one `gw1view` with `Cookie: sessid=…` → 15,286
bytes. **NO-GO:** if Phase 1 already produces this, **skip Phase 3 entirely.** It is insurance,
not the fix.

---

### Phase 4 — SSL certificates (30 min, evidence only)

We already know this is not the problem: `ssl_verify_result=0`, valid chain, no `-k` needed, HSTS
present. Implement it as a **logging, host-scoped** handler so we can prove it never fires:

```dart
onReceivedServerTrustAuthRequest: (controller, challenge) async {
  final host = challenge.protectionSpace.host;
  debugPrint('SSL challenge from $host');          // expect: never logs
  if (host == 'univenierp01.univen.ac.za') {
    return ServerTrustAuthResponse(
        action: ServerTrustAuthResponseAction.PROCEED);
  }
  return ServerTrustAuthResponse(
      action: ServerTrustAuthResponseAction.CANCEL);
},
```

**Rules:** scope it to the single host. Never blanket-accept. If this handler *does* fire, stop
and dump the certificate chain — that would be a genuine new finding (likely a MITM on the
tablet's Wi-Fi, e.g. a school/campus proxy).

Note: `webview_flutter`'s equivalent is `onSslAuthError` with `SslAuthError.proceed()` — available
in 4.14.1, so Phase 4 does **not** require the migration.

---

### Phase 5 — Referer (30 min, low priority)

We measured that Referer changes nothing at the HTML level (all 200). The only remaining place it
could matter is a **POST to `gw1proc`**, where a session guard might check the origin. So:

* Send `Referer: https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view` on the startup
  load (same-origin referer is the most "normal" value).
* Do **not** send `https://www.univen.ac.za/apply/` to the ERP host — a cross-origin referer is
  the unusual case, and we do not need it.
* If a POST still fails, capture the full request (method, URL, headers, body) with
  `cdp_network_requests` and compare byte-for-byte with a working Chrome session.

**GO:** the POST's status is 200 and the wizard advances to the next page.

---

### Phase 6 — POST / navigation semantics (1–2 h)

Only if the wizard advances but a later "Next" 404s.

* Audit `buildNavigationFixScript`. Its `window.location.assign()` click hijack is the suspect
  (RC-8). Replace the click hijack with an `action` rewrite on the form itself:

```js
document.addEventListener('submit', function (e) {
  var f = e.target;
  if (!f || f.tagName !== 'FORM') return;
  var a = f.getAttribute('action') || '';
  var fixed = a.replace(/gen\.gw1pkg\.gw1p(?:r|ro)?$/, 'gen.gw1pkg.gw1proc')
               .replace(/gen\.gw1pkg\.gw1v(?:i|ie)?$/, 'gen.gw1pkg.gw1view');
  if (fixed !== a) f.setAttribute('action', fixed);
}, true);   // capture, but let the browser submit
```

* Never rewrite a URL that is already complete. `ItsUrl.expandProcedure` is idempotent — keep it
  that way and unit-test it.
* Leave `apply_interceptor.dart` alone unless it is caught in the act.

**GO:** "Next" on the POPI page lands on the next wizard step with HTTP 200 and no
`wizard_access.html`.

---

### Phase 7 — Fallback (do not skip designing this)

If the embedded WebView still cannot hold the session after Phases 1–6, ship a **known-good
escape hatch** instead of another week of guessing:

* Primary: embedded WebView (as fixed above).
* Fallback button: **"Open in Chrome"** via `launchUrl(uri, mode: LaunchMode.externalApplication)`.
  Chrome on the same tablet shares the same network and will almost certainly work — which also
  becomes the control in our experiments.
* Long-term option: **Chrome Custom Tabs** (`flutter_custom_tabs`), which gives a real browser
  cookie jar with an in-app feel, and no WebView fingerprint differences at all.

Something that always works beats something clever that sometimes works.

---

## 6. Python / ACEsi tooling for traffic inspection

### 6.1 What ACEsi already has (no code changes needed)

| Tool | Use it for | Notes |
|---|---|---|
| `cdp_connect()` | Attach to the WebView/Chrome DevTools target | Requires Phase 0.2 — the current `main.dart` call enables the *wrong* plugin |
| `cdp_status()` | Confirm the attach + target list | Run first |
| `cdp_navigate(url, wait=True, wait_for="network_idle", timeout=30, idle_ms=500)` | Drive the **real** navigation so CDP records it as a Document request | `network_idle` matters here: the wizard polls |
| `cdp_network_requests(filter_status="404", filter_url="prodi41", limit=100)` | The 404 list, with status + headers | Our primary evidence tool |
| `cdp_get_response_body(url_contains="gw1view", max_chars=4000)` | Read the body of the failing response | Must be called **before** the next navigation (Chrome evicts bodies) |
| `cdp_evaluate(expr="document.cookie")` | Is `sessid` there at all? | Fastest discriminator |
| `cdp_console_logs()` | The `redirectme()` redirect and any JS exceptions | The 4,832-byte stub announces itself here |
| `cdp_dom_state()` | Read the rendered page text | Distinguish "Access Denied" from "cannot find detail" |
| `ui_screenshot(name="its_login")` | Visual proof on the tablet | For the before/after in the commit message |
| `ui_dump()` | Find the WebView's accessibility text | Useful when CDP is unavailable |
| `ui_tap(x, y)` / `ui_type(text)` | Drive the flow if DOM automation fails | |
| `curl(url, method, timeout, verify, allow_redirects)` | Server reachability, status only | **Limitation:** sends `User-Agent: Mozilla/5.0 (ACEsi curl)`, **no cookie jar**, **no custom headers**, so it cannot reproduce the `sessid` handshake |
| `webfetch(url)` | Fetch `/itsdocs/wizard_access.html` and the static assets | Useless for the session flow — it is a static page |
| `web_search(query)` | Oracle `gw1pkg` / `gw1startup` documentation | Low yield, but cheap |

**Order of operations that actually works:**

```
cdp_status()
cdp_connect()
cdp_console_logs()                    # snapshot before
cdp_navigate(startup_url, wait_for="network_idle")
cdp_network_requests(filter_url="prodi41")
cdp_evaluate("document.cookie")
cdp_evaluate("location.href")
cdp_get_response_body(url_contains="gw1view")
```

### 6.2 A standalone probe script (proposed, new file — not a `server.py` change)

`tool_curl` cannot do the handshake because it has no cookie jar and no header control. Tomorrow,
add a throwaway script at `tools/its_probe.py` (outside `server.py`, no impact on ACEsi) that
does the full matrix and prints one table:

```python
# proposed: tools/its_probe.py  — read-only diagnostic, deletes nothing
import http.cookiejar, urllib.request, re, sys

HOST = "https://univenierp01.univen.ac.za"
START = HOST + "/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP"
VIEW  = HOST + "/pls/prodi41/gen.gw1pkg.gw1view"

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def get(url, headers=None, method="GET", data=None):
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=headers or {})
    try:
        with opener.open(req, timeout=30) as r:
            body = r.read()
            return r.status, len(body), body, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, len(e.read()), b"", url

# 1. handshake
s, n, body, final = get(START)
print(f"startup  -> {s} {n}B final={final} cookies={[c.name for c in jar]}")
print("sessid in body:",
      bool(re.search(rb"setCookie\('sessid'", body)))

# 2. view with the jar (cookie now present)
s, n, body, final = get(VIEW, headers={"Referer": START})
print(f"view     -> {s} {n}B final={final}")
print("access-denied" if b"wizard_access" in body else "REAL PAGE" if n > 10000 else "stub")

# 3. matrix: which header changes the outcome?
for name, hdrs in {
    "no-referer": {},
    "same-origin-referer": {"Referer": VIEW},
    "cross-origin-referer": {"Referer": "https://www.univen.ac.za/apply/"},
    "desktop-ua": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"},
    "webview-ua": {"User-Agent": "Mozilla/5.0 (Linux; Android 11; SM-T515; wv) AppleWebKit/537.36 Chrome/155.0.0.0 Mobile Safari/537.36"},
}.items():
    jar.clear()                      # each row starts cold
    get(START)
    s, n, body, final = get(VIEW, headers=hdrs)
    print(f"{name:22s} -> {s} {n}B  {'DENIED' if b'wizard_access' in body else 'ok'}")
```

This is the script that ends the argument: it isolates **which single variable** changes the
outcome, with a fresh session per row. Run it on the PC **and** on the tablet (via `adb shell`
+ `python` is not available; instead reproduce the same rows in Chrome DevTools).

### 6.3 `adb` / `logcat` one-liners

```powershell
# The app's live network chatter (flutter debugPrint + WebView)
adb -s R52N518ESBE logcat -s flutter chromium "*:S"

# Watch for cookie/session decisions
adb -s R52N518ESBE logcat | Select-String "sessid|cookie|ITS|gw1"

# Confirm which URL the WebView actually committed
adb -s R52N518ESBE shell dumpsys activity top | Select-String "url="

# Force-stop and cold-start the app for a clean session test
adb -s R52N518ESBE shell am force-stop com.lipsyncstudent.lipsyncstudent
```

### 6.4 Optional heavy artillery: mitmproxy

Only if Phases 1–6 fail and we need to see the exact bytes:

```powershell
pip install mitmproxy
mitmproxy --listen-port 8080
adb -s R52N518ESBE shell settings put global http_proxy 10.0.2.2:8080
# install the mitm CA on the tablet, then:
#   Settings → Security → Encryption & credentials → Install a certificate → CA certificate
# UNDO afterwards:
adb -s R52N518ESBE shell settings put global http_proxy :0
```

Caveat: the app pins nothing today, so this will work — but the TLS cert would then be invalid,
which is precisely why Phase 4's scoped handler exists. **Revert the proxy when done.**

---

## 7. Verification checklist (definition of done)

Run all of these before declaring victory.

- [ ] **Server-side sanity** (PC, no app involved):
  `curl -sS -o NUL -w "%{http_code} %{size_download}" "https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP"`
  → `200 3096`
- [ ] **Handshake+view** (`tools/its_probe.py`) → `view -> 200 15286B` and `REAL PAGE`
- [ ] **Cold start, 3×**: force-stop → open UNIVEN → Apply → POPI page every time
- [ ] **No denial page**: `cdp_evaluate("location.href")` never contains `wizard_access.html`
- [ ] **Cookie present**: `cdp_evaluate("document.cookie")` contains `sessid=`
- [ ] **Exactly one** startup request per cold start (no redirect loop)
- [ ] **No truncated 404s** in `cdp_network_requests(filter_status="404")`
- [ ] **No spurious SSL challenges** in logcat
- [ ] **Advance**: tap Next → next wizard step, HTTP 200
- [ ] **Autofill** populates `oapReturnIDNo` / `oapReturnPPNo` when the profile has them
- [ ] **Release build** installs and still reaches the portal (proves `INTERNET` in the main manifest)
- [ ] **Fallback** "Open in Chrome" still works and is visible

---

## 8. Rollback

* Safe point: branch `fix-profile-dropdown`, commit **`1a13d62`**.
  `git stash` or `git reset --hard 1a13d62` gets us back.
* ⚠️ **The LipSyncStudent rename is currently uncommitted.** Commit it *before* touching the
  WebView, otherwise a hard reset will also throw away the rename.
* Suggested first action tomorrow:
  ```
  git add -A
  git commit -m "Rename to LipSyncStudent (pubspec, imports, Android/iOS labels)"
  git checkout -b its-portal-fix
  ```
* Known-bad commits to never cherry-pick back: `39677dd` (fetch hijack), `f70c4a7` (clearCookies +
  mobile UA), `0c9ebf6`'s *removal* is good but the reasoning stands — no `x_processcode` on
  `gw1view`.

---

## 9. Risks, traps, and "do not" list

**Traps**

1. **`/` returns 403.** Any warm-up that touches the portal root looks like a block. Use
   `gw1startup` only.
2. **The 4,832-byte stub is not a WAF page.** It is a session killer that deletes `sessid`.
   Retrying from it makes things worse.
3. **`parent.location.replace`.** The wizard expects a frameset. Our top-level load is correct,
   but any JS we inject must not re-parent or re-host the document.
4. **Two backends.** Responses carry both `Via: 1.1 univenperp01` and `Via: 1.1 univenierp01`.
   A session created on one and validated on the other can evaporate. If cookies look right but
   the stub comes back, suspect this.
5. **The forced desktop UA** makes the server serve desktop markup that a touch UI struggles to
   drive. Removing it is both more honest and more testable.
6. **`x_stmp` in `gen.gw1pkg.gw1gettags?...&x_stmp=261026...`** — sub-resource calls carry a
   timestamp. If those 404, the page renders but buttons silently do nothing. Check them
   explicitly in the request log.

**Do not**

- ❌ Warm up on `https://univenierp01.univen.ac.za/` (403).
- ❌ Call `clearCookies()` in the ITS flow.
- ❌ Add `x_processcode` to `gw1view` (404).
- ❌ Spoof a User-Agent "to get past the WAF" — measured, does nothing.
- ❌ Blanket-accept SSL for all hosts.
- ❌ Resurrect the `fetch` + `document.write` POST hijack.
- ❌ Rewrite `gw1proc` requests.
- ❌ Assume "Access Denied" means an external firewall. It means *no session*.

---

## 10. Suggested schedule

| Time | Phase | Exit criterion |
|---|---|---|
| 09:00–09:45 | 0 — ground truth | Know whether Chrome on the tablet can reach the POPI page |
| 09:45–11:30 | 1 — entry point | POPI page loads in the app, no `wizard_access.html` |
| 11:30–12:30 | 2 — session survival | 3/3 cold starts succeed |
| 13:30–15:30 | 3 — header interception *(only if needed)* | Clean one-startup-one-view chain |
| 15:30–16:00 | 4 + 5 — SSL/Referer *(evidence)* | Handler never fires; POST 200 |
| 16:00–17:00 | 6 — POST semantics *(only if needed)* | "Next" advances |
| 17:00–17:30 | 7 — fallback + commit | Release build + rollback documented |

**Hard stop rule:** if Phase 1 has not produced the 15,286-byte page by 12:00, stop coding and
spend the afternoon on `tools/its_probe.py` + the Chrome control experiment. The answer will be in
the request log, not in another guess.

---

## Appendix A — Raw evidence from the probe session

```
GET /                                            -> 403  199B   Apache
GET /pls/prodi41/gen.gw1pkg.gw1view              -> 200 4832B   "cannot find detail" -> wizard_access.html
GET /pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP -> 200 3096B  sets sessid, replaces location
GET /pls/prodi41/gen.gw1pkg.gw1view + sessid     -> 200 15286B  REAL WIZARD (frmOne, ITS_OAP_START)
GET /pls/prodi41/gen.gw1pkg.gw1v                 -> 404  210B
GET /pls/prodi41/gen.gw1pkg.gw1p                 -> 404  210B
GET /pls/prodi41/gen.gw1pkg.gw1                  -> 404  209B
GET /pls/prodi41/gen.gw1pkg.gw1view?x_processcode=ITS_OAP -> 404 213B
GET /itsdocs/wizard_access.html                  -> 200  "Access Denied — A serious security exception…"

Headers of a good response:
  Server: Oracle-HTTP-Server-12c
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Frame-Options: SAMEORIGIN
  X-Content-Type-Options: nosniff
  X-XSS-Protection: 1; mode=block
  Via: 1.1 univenperp01.univen.ac.za
  Via: 1.1 univenierp01.univen.ac.za
  Content-Type: text/html; charset=UTF-8
  (no WAF/CDN headers of any kind)

TLS: ssl_verify_result=0, ALPN http/1.1, no custom CA needed.
```

## Appendix B — Live field IDs on the real wizard page (autofill targets)

```
frmOne
oapAcceptPopi / oapAcceptPopi_ChkBx / oapNotAcceptPopi / oapNotAcceptPopi_ChkBx
oapReturnIDNo / oapReturnPPNo / oapOldNew / oapOldNew_desc
oapNextBtn1 / oapReturnBtn
genericErrorDiv
#ITS_OAP  (process container)
```

These come from the 15,286-byte page served **with** a valid `sessid` — i.e. exactly the page we
are trying to reach. Autofill for the POPI step should target the `oap*` names above, not the
older `P_*` guesses.
