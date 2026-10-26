import 'dart:io';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:lipsyncstudent/services/autofill_script.dart' as star;
import 'package:lipsyncstudent/services/its_url_fixer.dart';
import 'package:url_launcher/url_launcher.dart';

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
  bool _loading = true;
  String? _currentUrl;
  String? _profileJson;
  bool _wizardBootstrapped = false;

  @override
  void initState() {
    super.initState();
    _profileJson = widget.profileJson;

    final initialUrl = _resolveInitialUrl();
    _currentUrl = initialUrl;

    _controller = WebViewController();

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

    // The User-Agent is deliberately left at the WebView default: Chrome on
    // this same tablet reaches the wizard with its normal mobile UA, so
    // spoofing a desktop UA is both unnecessary and unlike the known-good
    // control.
    _controller.setJavaScriptMode(JavaScriptMode.unrestricted);

    _controller.setNavigationDelegate(
      NavigationDelegate(
        onPageStarted: (url) {
          _currentUrl = url;
          if (mounted) setState(() => _loading = true);
        },
        onPageFinished: (url) async {
          _currentUrl = url;
          if (mounted) setState(() => _loading = false);

          // gw1startup sets `sessid` from inline JS and then redirects itself
          // to gw1view. If that redirect did not happen, finish the handshake
          // ourselves now that the cookie is in place. This is the only place
          // we jump to the wizard URL explicitly.
          if (url.contains('gw1startup')) {
            await _continueToWizardIfNeeded();
          }

          await _injectPageScripts();
        },
        onHttpError: (error) {
          debugPrint(
            'WebView HTTP ${error.response?.statusCode} ${error.request?.uri}',
          );
        },
        onWebResourceError: (error) {
          debugPrint(
            'WebView error: ${error.description} (${error.errorCode})',
          );
        },
      ),
    );

    _controller.loadRequest(Uri.parse(initialUrl));
  }

  @override
  void didUpdateWidget(covariant UniversityWebViewScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.profileJson == oldWidget.profileJson) return;

    // The profile finished loading after this screen opened. onPageFinished
    // will not fire again for the page already on screen, so inject now or the
    // star button never appears. Re-injection is safe: both scripts de-dup.
    _profileJson = widget.profileJson;
    if (!_loading) _injectPageScripts();
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: Colors.blue,
        actions: [
          IconButton(
            icon: const Icon(Icons.open_in_browser),
            tooltip: 'Open in Chrome',
            onPressed: _openInExternalBrowser,
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
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading)
            const LinearProgressIndicator(
              backgroundColor: Colors.transparent,
            ),
        ],
      ),
    );
  }
}
