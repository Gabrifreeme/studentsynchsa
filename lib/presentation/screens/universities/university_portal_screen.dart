import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;
import 'package:studentsyncsa/services/its_url_fixer.dart';

class UniversityPortalScreen extends StatefulWidget {
  final String universityName;
  final String url;
  final StudentProfile? profile;

  const UniversityPortalScreen({
    super.key,
    required this.universityName,
    required this.url,
    this.profile,
  });

  @override
  State<UniversityPortalScreen> createState() => _UniversityPortalScreenState();
}

class _UniversityPortalScreenState extends State<UniversityPortalScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  StudentProfile? _profile;
  String? _profileJson;
  bool _isUniven = false;

  @override
  void initState() {
    super.initState();
    _profile = widget.profile;
    if (_profile != null) {
      _profileJson = jsonEncode(_profile!.toJson());
    }
    _isUniven = widget.universityName.toUpperCase() == 'UNIVEN';
    _loadProfileIfMissing();

    // DO NOT clearCookies() here — it races with the page load and can destroy
    // the APEX session cookie the portal just set, causing 404 on form submit.

    // Determine initial URL
    String initialUrl = ItsUrl.normalize(widget.url);
    if (_isUniven) {
      initialUrl =
          'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view';
    }

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(true)
      ..setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      )
      ..addJavaScriptChannel(
        'FlutterNavigation',
        onMessageReceived: (JavaScriptMessage message) {
          final targetUrl = message.message;
          debugPrint('🔴 JavaScript navigation: $targetUrl');
          if (targetUrl.startsWith('http') && mounted) {
            _controller.loadRequest(Uri.parse(ItsUrl.normalize(targetUrl)));
          }
        },
      )
      ..addJavaScriptChannel(
        'FlutterLog',
        onMessageReceived: (JavaScriptMessage message) {
          debugPrint('🟢 JS: ${message.message}');
        },
      );

    if (_controller.platform is AndroidWebViewController) {
      final androidController =
          _controller.platform as AndroidWebViewController;
      androidController.setTextZoom(150);
      // NOTE: webview_flutter 4.13+ hardcodes `setSupportMultipleWindows(true)`
      // internally on AndroidWebViewController and no longer exposes a Dart
      // toggle for it (the old `setSupportMultipleWindows(false)` call no longer
      // compiles). Keeping target=_blank popups in-window and routing every
      // navigation through ITS-URL normalization is handled by
      // `onNavigationRequest` below + the injected navigation-fix script
      // (`buildNavigationFixScript`), so this toggle is not required.
    }

    _controller
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (request) {
            final url = request.url.toString();
            debugPrint('🟡 Navigation: $url');

            // Normalize any malformed ITS URL before it reaches the portal:
            // truncated procedure name (gw1v -> gw1view), host typo
            // (unlven/univenerp01), and plain http -> https. The gw1proc/gw1p
            // POST path is handled by the JS fetch hijack in
            // buildNavigationFixScript — do NOT GET-reload it.
            if (ItsUrl.isItsHost(url)) {
              final fixed = ItsUrl.normalize(url);
              final isPostHandler =
                  url.contains('gw1proc') || url.contains('gen.gw1pkg.gw1p');
              if (fixed != url && !isPostHandler) {
                debugPrint('🔧 Expanding truncated ITS URL: $url -> $fixed');
                _controller.loadRequest(Uri.parse(fixed));
                return NavigationDecision.prevent;
              }
            }

            return NavigationDecision.navigate;
          },
          onPageStarted: (url) {
            debugPrint('📄 Page started: $url');
            setState(() => _loading = true);
          },
          onPageFinished: (url) async {
            debugPrint('✅ Page finished: $url');
            setState(() => _loading = false);

            // Last-line recovery: if the committed URL is still a truncated
            // gw1v, reload the expanded URL once (guarded against loops).
            if (_recoverTruncatedPage(url)) return;

            // Inject navigation fix
            try {
              await _controller.runJavaScript(star.buildNavigationFixScript());
            } catch (e) {
              debugPrint('Navigation fix error: $e');
            }
          },
          onWebResourceError: (error) {
            debugPrint('❌ Error: ${error.description}');
          },
        ),
      )
      ..loadRequest(Uri.parse(initialUrl));
  }

  Future<void> _loadProfileIfMissing() async {
    if (_profile != null) return;

    final repo = ProfileRepositoryImpl();
    var p = await repo.getProfile();
    if (p == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      p = await repo.getProfile();
    }
    if (p == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      p = await repo.getProfile();
    }
    if (p != null && mounted) {
      setState(() {
        _profile = p;
        _profileJson = jsonEncode(p?.toJson());
      });
    }
  }

  String? _lastRecovered;
  DateTime? _lastRecoveredAt;

  /// Recover from a truncated ITS GET target that committed anyway (the
  /// truncation happened below onNavigationRequest). Returns true when a
  /// reload of the corrected URL was issued.
  bool _recoverTruncatedPage(String url) {
    if (!ItsUrl.isItsHost(url)) return false;
    if (!url.contains('gen.gw1pkg.gw1v') || url.contains('gw1view')) return false;
    final fixed = ItsUrl.normalize(url);
    if (fixed == url) return false;
    final now = DateTime.now();
    if (_lastRecovered == fixed &&
        _lastRecoveredAt != null &&
        now.difference(_lastRecoveredAt!) < const Duration(seconds: 5)) {
      return false;
    }
    _lastRecovered = fixed;
    _lastRecoveredAt = now;
    debugPrint('🔧 Recovering truncated ITS page: $url -> $fixed');
    _controller.loadRequest(Uri.parse(fixed));
    return true;
  }

  void _openInChrome() async {
    String url = widget.url;
    if (_isUniven) {
      url = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view';
    }
    url = ItsUrl.normalize(url);

    try {
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
        debugPrint('✅ Opened in Chrome: $url');
      }
    } catch (e) {
      debugPrint('❌ Error opening Chrome: $e');
    }
  }

  void _showAutofillConfirmDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Text('⭐', style: TextStyle(fontSize: 28)),
            SizedBox(width: 8),
            Text('Auto-fill Form'),
          ],
        ),
        content: const Text(
          "You like me to try and auto fill this page?",
          style: TextStyle(fontSize: 16),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('No'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.of(ctx).pop();
              await _runAutofill();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.amber.shade700,
            ),
            child: const Text('Yes', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  Future<void> _runAutofill() async {
    try {
      // Load autofill script on demand
      if (_profileJson != null) {
        await _controller.runJavaScript(
          star.buildAutofillScript(_profileJson!),
        );
        await _controller.runJavaScript(
          star.buildRemoveOldPostalPickerScript(),
        );
        await _controller.runJavaScript(
          star.buildPostalCodePickerScript(_profileJson!),
        );
      }
      await _controller.runJavaScript(
        'if (typeof requestFlutterAutofill === "function") requestFlutterAutofill();',
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ Auto-fill triggered!'),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      debugPrint('❌ Autofill error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Auto-fill failed: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  void _showGuidanceDialog() {
    final steps = [
      'Click "Apply Now" or the red APPLY button on the page',
      'Enter your South African ID number',
      'Fill in your personal details (name, DOB, gender)',
      'Enter your contact information (phone, email, address)',
      'Provide your academic history and subjects',
      'Upload required documents (ID, results, proof)',
      'Review all information carefully',
      'Submit your application and SAVE your student number!',
    ];

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Text('⭐', style: TextStyle(fontSize: 28)),
            SizedBox(width: 8),
            Text('Application Guide'),
          ],
        ),
        content: SizedBox(
          width: double.maxFinite,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ...steps.map(
                (step) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${steps.indexOf(step) + 1}.',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(width: 6),
                      Expanded(child: Text(step)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.red.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade200),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.warning, color: Colors.red, size: 16),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '⚠️ IMPORTANT: Save your student number after submission!',
                        style: TextStyle(fontSize: 12, color: Colors.red),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blue.shade200),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info, color: Colors.blue, size: 16),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '💡 Need autofill? Tap "Open in Chrome" for better form filling.',
                        style: TextStyle(fontSize: 12, color: Colors.blue),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Close'),
          ),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.pop(ctx);
              _openInChrome();
            },
            icon: const Icon(Icons.open_in_browser, size: 16),
            label: const Text('Open in Chrome'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: Colors.blue.shade800,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.star, color: Colors.amber, size: 30),
            onPressed: _showAutofillConfirmDialog,
            tooltip: 'Auto-fill form',
          ),
          IconButton(
            icon: const Icon(Icons.open_in_browser),
            onPressed: _openInChrome,
            tooltip: 'Open in Chrome (Recommended for forms)',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _controller.reload(),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading) const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
