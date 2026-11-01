import 'dart:io';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:lipsyncstudent/services/autofill_script.dart' as star;
import 'package:lipsyncstudent/services/its_url_fixer.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:lipsyncstudent/presentation/screens/profile/quick_copy_screen.dart';

/// Shows a university's web portal.
///
/// UNIVEN's Oracle ITS wizard is special: the only URL that creates the
/// server-side session is
/// `gen.gw1pkg.gw1startup?x_processcode=ITS_OAP`. Loading
/// `gen.gw1pkg.gw1view` directly returns a stub that deletes the `sessid`
/// cookie and redirects to `/itsdocs/wizard_access.html` ("Access Denied").
/// So every ITS deep link is bootstrapped through the startup URL first, and
/// the wizard page is only loaded once that cookie exists.
class UniversityWebViewScreen extends StatefulWidget {
  final String universityName;
  final String url;
  final String? profileJson;

  const UniversityWebViewScreen({
    super.key,
    required this.universityName,
    required this.url,
    this.profileJson,
  });

  @override
  State<UniversityWebViewScreen> createState() => _UniversityWebViewScreenState();
}

class _UniversityWebViewScreenState extends State<UniversityWebViewScreen> {
  /// Creates the ITS server session and sets the `sessid` cookie.
  static const String _itsStartupUrl =
      'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP';

  /// The wizard itself. Only valid once [_itsStartupUrl] has run.
  static const String _itsWizardUrl =
      'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view';

  late WebViewController _controller;
  late WebViewController _acesiController;
  bool _loading = true;
  String? _currentUrl;
  String? _profileJson;
  bool _wizardBootstrapped = false;
  bool showAcesi = false;

  @override
  void initState() {
    super.initState();
    _profileJson = widget.profileJson;

        final initialUrl = 'https://apply.ufs.ac.za/Application/Start';
    _currentUrl = initialUrl;

    _controller = WebViewController();
    // Single UA, set once. The UA does not affect UFS markup (the portal
    // returns the same HTML for desktop and mobile agents), so this only
    // exists to avoid the "unsupported browser" path some other portals take.
    // Note the engine is whatever Android System WebView ships, which may be
    // older than the version advertised here.
    _controller.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    );

    // Android specific settings (cookies & media).
    if (Platform.isAndroid) {
      final androidController =
          _controller.platform as AndroidWebViewController;
      androidController.setMediaPlaybackRequiresUserGesture(false);

      final cookieManager = AndroidWebViewCookieManager(
        const PlatformWebViewCookieManagerCreationParams(),
      );
      cookieManager.setAcceptThirdPartyCookies(androidController, true);
    }

    _controller.setJavaScriptMode(JavaScriptMode.unrestricted);

    _controller.setNavigationDelegate(
      NavigationDelegate(
                onSslAuthError: (SslAuthError error) async {
          debugPrint('SSL override: $error');
          await error.proceed();
        },
        onPageStarted: (url) {
          _currentUrl = url;
          if (mounted) setState(() => _loading = true);
        },
        onPageFinished: (url) async {
          _currentUrl = url;
          if (mounted) setState(() => _loading = false);
          debugPrint('PAGE finished: $url');

          // gw1startup sets `sessid` from inline JS and then redirects itself
          // to gw1view. If that redirect did not happen, finish the handshake
          // ourselves now that the cookie is in place. This is the only place
          // we jump to the wizard URL explicitly.
          if (url.contains('gw1startup')) {
            await _continueToWizardIfNeeded();
          }
          
          // The grey sheet is not a modal, not a loading mask, and not an
          // element you can query for. It is a pseudo-element from the SB
          // Admin Pro theme shipped as /lib/sbpro/css/styles.css:
          //
          //   .sidenav-toggled #layoutSidenav #layoutSidenav_content:before {
          //     content: ""; position: absolute; top: 0; left: 0;
          //     width: 100%; height: 100%; background: #000;
          //     z-index: 1037; opacity: 0.5;
          //   }
          //
          // The portal hard-codes class="nav-fixed sidenav-toggled" on <body>.
          // SB Admin Pro hides that overlay for widths >= 992px only, so on a
          // phone it paints a 50% black sheet over the entire page - the text
          // shows through, nothing is clickable. Because it is a ::before there
          // is no matching DOM node, which is why every class-based CSS rule
          // and every "full screen overlay" sweep missed it.
          await _fixSidenavVeil();
        },
        onHttpError: (error) {
          debugPrint(
            'WebView HTTP ${error.response?.statusCode} ${error.request?.uri}',
          );
        },
               onWebResourceError: (error) async {
          debugPrint('WebView error: ${error.description} (${error.errorCode})');
          // Sub-resource failures (images, scripts, XHR) are not fatal and
          // must NOT bounce the user into Chrome. Only a main-frame failure
          // is worth escaping to an external browser.
          if (error.isForMainFrame != true) return;
          final current = _currentUrl;
          if (current == null) return;
          final url = Uri.parse(current);
          if (await canLaunchUrl(url)) {
            await launchUrl(url, mode: LaunchMode.externalApplication);
          }
        },
      ),
    );

    _controller.loadRequest(Uri.parse(initialUrl));

    // ACESi assistant WebView (black/amber theme, localhost:5000)
    _acesiController = WebViewController();
    _acesiController.setJavaScriptMode(JavaScriptMode.unrestricted);

    _acesiController.setNavigationDelegate(
      NavigationDelegate(
        onPageFinished: (url) async {
                          try {
          String css = "body,html,div,table,td,tr{background-color:#000000!important;color:#ff9d00!important;font-family:monospace!important;}"
                       "input,select,textarea{background-color:#111111!important;color:#ff9d00!important;border:1px solid #ff9d00!important;border-radius:4px!important;padding:4px!important;}"
                       "a{color:#ff9d00!important;text-decoration:none!important;}"
                       "button,input[type='submit']{background-color:#000000!important;color:#ff9d00!important;border:1px solid #ff9d00!important;border-radius:6px!important;padding:8px 16px!important;font-weight:bold!important;}";
          
          // Using backticks to safely wrap the CSS string for JavaScript
          String js = "var style=document.createElement('style'); style.innerHTML=\`" + css + "\`; document.head.appendChild(style);";
          
          await _acesiController.runJavaScript(js);
        } catch (e) {
          debugPrint('CSS Injection Error: $e');
        } 
        },
      ),
    );
    _acesiController.loadRequest(Uri.parse('http://127.0.0.1:5000'));
  }

  @override
  void didUpdateWidget(covariant UniversityWebViewScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.profileJson == oldWidget.profileJson) return;

    // The profile finished loading after this screen opened. onPageFinished
    // will not fire again for the page already on screen, so inject now or the
    // star button never appears. Re-injection is safe: both scripts de-dup.
    _profileJson = widget.profileJson;
  }

  /// True when this screen is showing UNIVEN's Oracle ITS wizard.
  bool get _isUnivenIts {
    final raw = widget.url.toLowerCase();
    return raw.contains('univenierp01') ||
        raw.contains('/pls/prodi41') ||
        widget.universityName.toUpperCase().contains('UNIVEN');
  }

  /// Returns the URL to open first.
  ///
  /// For UNIVEN/ITS any entry point other than `gw1startup` is rewritten to
  /// the startup URL, because a cold `gw1view` load can never succeed. Other
  /// universities and funding portals are left untouched.
  String _resolveInitialUrl() {
    final raw = widget.url.trim();
    if (raw.isEmpty) return _itsStartupUrl;

    final normalized = ItsUrl.normalize(raw);
    if (!_isUnivenIts) return normalized;

    // Already the session-creating entry point.
    if (normalized.contains('gw1startup')) return normalized;

    // gw1view, a truncated gw1v/gw1p, or any other deep link: bootstrap first.
    return _itsStartupUrl;
  }

  /// Completes the startup -> wizard handshake if the page did not do it.
  Future<void> _continueToWizardIfNeeded() async {
    if (_wizardBootstrapped) return;
    _wizardBootstrapped = true;

    // Give the startup page's inline `location.replace(...)` a moment to run.
    await Future<void>.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;

    // A real navigation already happened - nothing to do.
    final current = _currentUrl;
    if (current == null || !current.contains('gw1startup')) return;

    // Belt and braces: confirm the document is still on the startup page.
    try {
      final live = await _controller.runJavaScriptReturningResult('location.href');
      if (!live.toString().contains('gw1startup')) return;
    } catch (_) {
      // If the location cannot be read, fall through and load the wizard.
    }

    if (!mounted) return;
    await _controller.loadRequest(Uri.parse(_itsWizardUrl));
  }

  /// Reports what is actually painted on top of the portal page.
  ///
  /// A `::before` pseudo-element never appears in `querySelectorAll`, so the
  /// only reliable evidence is (a) the computed style of the pseudo-element on
  /// its host, and (b) `elementsFromPoint`, which shows whether the topmost
  /// hit at screen centre is the host itself (pseudo-element on top) or one of
  /// its children (no veil).
  static const String _veilProbeJs = r'''
    (function () {
      function info(el) {
        if (!el) return null;
        var c = getComputedStyle(el), r = el.getBoundingClientRect();
        return { t: el.tagName, id: el.id || '',
                 c: String(el.className || '').slice(0, 70),
                 p: c.position, z: c.zIndex, bg: c.backgroundColor,
                 op: c.opacity, pe: c.pointerEvents,
                 box: [r.left | 0, r.top | 0, r.width | 0, r.height | 0] };
      }
      var host = document.getElementById('layoutSidenav_content');
      var before = null;
      if (host) {
        var b = getComputedStyle(host, '::before');
        before = { content: b.content, display: b.display,
                   bg: b.backgroundColor, op: b.opacity, z: b.zIndex,
                   pos: b.position, w: b.width, h: b.height };
      }
      var out = {
        url: location.href,
        iw: window.innerWidth, ih: window.innerHeight,
        cw: document.documentElement.clientWidth,
        dpr: window.devicePixelRatio,
        ready: document.readyState,
        bodyClass: document.body ? document.body.className : null,
        hostFound: !!host,
        before: before,
        nav: info(document.getElementById('layoutSidenav_nav')),
        injected: !!document.getElementById('ufs-veil-fix'),
        stack: []
      };
      try {
        out.stack = (document.elementsFromPoint(
          (window.innerWidth / 2) | 0,
          (window.innerHeight / 2) | 0) || []).slice(0, 5).map(info);
      } catch (e) {}
      return JSON.stringify(out);
    })();
  ''';

  static const String _veilFixJs = r'''
    (function () {
      var result = { style: 'present', rulesDeleted: 0 };

      // 1. Override the dimmer via CSS.
      //
      // The width check lives INSIDE the stylesheet as a media query, on
      // purpose: `window.innerWidth` is not a usable proxy for one. This
      // tablet reports innerWidth 1096 (Chrome zoomed the page out) while the
      // layout viewport the theme's media query sees is 800 - so a JS
      // `innerWidth < 992` test silently skips exactly the case that needs
      // fixing. The browser evaluates both queries the same way, so let CSS
      // decide.
      if (!document.getElementById('ufs-veil-fix')) {
        var s = document.createElement('style');
        s.id = 'ufs-veil-fix';
        s.textContent =
          '.sidenav-toggled #layoutSidenav #layoutSidenav_content::before' +
          '{content:none!important;display:none!important;opacity:0!important;' +
          'background:transparent!important;}' +
          '@media (max-width: 991.98px){' +
          '.sidenav-toggled #layoutSidenav #layoutSidenav_nav' +
          '{transform:translateX(-15rem)!important;pointer-events:none!important;}' +
          '.sidenav-toggled #layoutSidenav #layoutSidenav_content' +
          '{margin-left:-15rem!important;}' +
          '}';
        (document.head || document.documentElement).appendChild(s);
        result.style = 'added';
      }

      // 2. Delete the offending rule from the stylesheet. Overriding is enough
      //    in theory; deleting cannot be beaten by a later sheet. Rules are
      //    indexed per sheet and @media blocks contain their own child rules,
      //    so compare per leaf rule - matching a media rule's cssText would
      //    wipe the entire breakpoint.
      function matches(rule) {
        var t = rule.cssText || '';
        return t.indexOf('layoutSidenav_content') !== -1 &&
               t.indexOf('before') !== -1;
      }
      for (var i = 0; i < document.styleSheets.length; i++) {
        var rules = null;
        try { rules = document.styleSheets[i].cssRules; } catch (e) { continue; }
        if (!rules) continue;
        for (var j = rules.length - 1; j >= 0; j--) {
          var r = rules[j];
          if (r.cssRules) {
            // @media / @supports / @layer wrapper: look inside only.
            for (var k = r.cssRules.length - 1; k >= 0; k--) {
              if (matches(r.cssRules[k])) {
                try { r.deleteRule(k); result.rulesDeleted++; } catch (e) {}
              }
            }
          } else if (matches(r)) {
            try { document.styleSheets[i].deleteRule(j); result.rulesDeleted++; }
            catch (e) {}
          }
        }
      }

      return JSON.stringify(result);
    })();
  ''';

  /// Removes SB Admin Pro's off-canvas dimmer on phone-width screens.
  ///
  /// The portal renders `<body class="nav-fixed sidenav-toggled">`, and the
  /// theme paints `#layoutSidenav_content::before` as a 50%-black, full-page
  /// sheet while that class is present. The theme only disables it at
  /// >= 992px (`@media (min-width: 992px) { ... :before { display: none } }`),
  /// so the desktop layout is clean while a phone gets an unclickable grey
  /// page. Cancelling the dimmer below that breakpoint restores the layout the
  /// theme intended for a phone: nav parked off-canvas, content full width,
  /// nothing intercepting taps.
  ///
  /// The width test lives inside the injected stylesheet as a media query, not
  /// in Dart/JS: on this tablet `window.innerWidth` reports 1096 while the
  /// layout viewport the theme's own query sees is 800, so a JS width check
  /// skips exactly the case that needs fixing.
  Future<void> _fixSidenavVeil() async {
    try {
      final fix = await _controller.runJavaScriptReturningResult(_veilFixJs);
      final after = await _controller.runJavaScriptReturningResult(_veilProbeJs);

      // One line on success; dump the full state only if the dimmer survived,
      // which is the one case worth reading in detail.
      if (after.toString().contains('"display":"block"')) {
        debugPrint('VEIL STILL DIMMED\n  fix: $fix\n  after: $after');
      } else {
        debugPrint('VEIL clear ($fix)');
      }
    } catch (e) {
      debugPrint('VEIL error: $e');
    }
  }

  Future<void> _injectPageScripts() async {
    try {
      await _controller.runJavaScript(star.buildNavigationFixScript());
    } catch (e) {
      debugPrint('Nav script error: $e');
    }

    final json = _profileJson;
    if (json == null || json.isEmpty) {
      debugPrint('Autofill skipped: no profile data on this screen');
      return;
    }
    try {
      await _controller.runJavaScript(star.buildAutofillScript(json));
    } catch (e) {
      debugPrint('Autofill error: $e');
    }
  }

  /// Where "Open in Chrome" should send the user.
  ///
  /// For ITS this is always the startup URL, even when the WebView is already
  /// on gw1view: a fresh browser has none of the WebView's cookies, and a cold
  /// gw1view load is exactly the "Access Denied" stub.
  Uri _externalLaunchUrl() {
    final current = _currentUrl;
    if (current != null && current.contains('gw1startup')) {
      return Uri.parse(current);
    }
    if (_isUnivenIts) return Uri.parse(_itsStartupUrl);
    return Uri.parse(current ?? _resolveInitialUrl());
  }

  /// Escape hatch: hand the portal to the device's real browser, which has its
  /// own trust store and cookie jar. Guaranteed to work even while the
  /// embedded WebView is being fixed.
  Future<void> _openInExternalBrowser() async {
    final uri = _externalLaunchUrl();
    try {
      final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched) {
        throw StateError('No browser accepted $uri');
      }
    } catch (e) {
      debugPrint('Open in browser failed: $e');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not open a browser: $e')),
      );
    }
  }

  Future<List<String>> _listLibFiles() async {
    final dir = Directory('lib');
    if (!await dir.exists()) return [];
    try {
      final entities = await dir.list(recursive: true).toList();
      final files = entities.whereType<File>().map((f) => f.path.replaceFirst('lib\\', '').replaceFirst('lib/', '')).toList()..sort();
      return files;
    } catch (_) { return []; }
  }

  void _openFileInCodeEditor(String relativePath) {
    try { Process.run('code', [relativePath]); } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: Colors.blue,
        actions: [
          // Magic wand: manual autofill trigger for testing.
          IconButton(
            icon: const Icon(Icons.auto_fix_high),
            tooltip: 'Test Autofill',
            onPressed: () async {
              final json = _profileJson;
              if (json == null || json.isEmpty) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('No profile loaded'),
                    backgroundColor: Colors.orange,
                    duration: Duration(seconds: 3),
                  ),
                );
                return;
              }
              try {
                await _controller.runJavaScript(
                  star.buildAutofillScript(json),
                );
                await _controller.runJavaScript(
                  'if (typeof window.requestFlutterAutofill === "function") '
                  'window.requestFlutterAutofill();',
                );
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Autofill triggered'),
                    backgroundColor: Colors.green,
                    duration: Duration(seconds: 2),
                  ),
                );
              } catch (e) {
                debugPrint('Test autofill error: $e');
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Autofill failed: $e'),
                    backgroundColor: Colors.red,
                    duration: Duration(seconds: 3),
                  ),
                );
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.open_in_browser),
            tooltip: 'Open in Chrome',
            onPressed: _openInExternalBrowser,
          ),
          IconButton(
            icon: const Icon(Icons.copy_all),
            tooltip: 'Quick Copy Profile',
            onPressed: () {
              Navigator.push(context, MaterialPageRoute(builder: (_) => QuickCopyScreen(profileJson: _profileJson, portalUrl: widget.url)));
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Reload',
            onPressed: () => _controller.reload(),
          ),
          IconButton(
            icon: const Icon(Icons.home),
            tooltip: 'Restart application',
            onPressed: () {
              _wizardBootstrapped = false;
              _controller.loadRequest(Uri.parse(_resolveInitialUrl()));
            },
          ),
          IconButton(
            tooltip: 'Toggle ACESi',
            onPressed: () {
              setState(() => showAcesi = !showAcesi);
            },
            icon: Column(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('ACE', style: TextStyle(color: Color(0xFFFF9D00), fontWeight: FontWeight.bold, height: 1.0, fontSize: 10)),
                Text('si', style: TextStyle(color: Color(0xFFFF9D00), fontWeight: FontWeight.bold, height: 1.0, fontSize: 10)),
                Text('â€¿', style: TextStyle(color: Color(0xFFFF9D00), fontWeight: FontWeight.bold, height: 1.0, fontSize: 14)),
              ],
            ),
          ),
        ],
      ),
      body: IndexedStack(
        index: showAcesi ? 1 : 0,
        children: [
          Stack(
            children: [
              WebViewWidget(controller: _controller),
              if (_loading)
                const LinearProgressIndicator(
                  backgroundColor: Colors.transparent,
                ),
            ],
          ),
          Row(
            children: [
              Container(
                width: 260,
                decoration: BoxDecoration(
                  color: Color(0xFF0a0a0a),
                  border: Border(right: BorderSide(color: Color(0xFFFF9D00), width: 1.5)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Padding(
                      padding: EdgeInsets.all(12),
                      child: Text('Explorer â€” lib/', style: TextStyle(color: Color(0xFFFF9D00), fontWeight: FontWeight.bold, fontSize: 14)),
                    ),
                    Expanded(
                      child: FutureBuilder<List<String>>(
                        future: _listLibFiles(),
                        builder: (context, snap) {
                          if (!snap.hasData) return const Center(child: CircularProgressIndicator(strokeWidth: 2));
                          final files = snap.data ?? [];
                          if (files.isEmpty) return const Padding(padding: EdgeInsets.all(12), child: Text('No lib/ files', style: TextStyle(color: Colors.grey)));
                          return ListView.builder(
                            itemCount: files.length,
                            itemBuilder: (context, i) {
                              final f = files[i];
                              return ListTile(
                                dense: true,
                                title: Text(f, style: TextStyle(color: Colors.white, fontSize: 12, fontFamily: 'monospace')),
                                onTap: () => _openFileInCodeEditor(f),
                              );
                            },
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(child: WebViewWidget(controller: _acesiController)),
            ],
          ),
        ],
      ),
    );
  }
}

