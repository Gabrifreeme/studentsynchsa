import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

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
  bool _isUniven = false;

  @override
  void initState() {
    super.initState();
    _profile = widget.profile;
    _isUniven = widget.universityName.toUpperCase() == 'UNIVEN';
    _loadProfileIfMissing();

    WebViewCookieManager().clearCookies();

    // Determine initial URL
    String initialUrl = widget.url;
    if (_isUniven) {
      initialUrl = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view';
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
            _controller.loadRequest(Uri.parse(targetUrl));
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
      final androidController = _controller.platform as AndroidWebViewController;
      androidController.setTextZoom(150);
    }

    _controller
      ..setNavigationDelegate(
        NavigationDelegate(
          onNavigationRequest: (request) {
            final url = request.url.toString();
            debugPrint('🟡 Navigation: $url');
            return NavigationDecision.navigate;
          },
          onPageStarted: (url) {
            debugPrint('📄 Page started: $url');
            setState(() => _loading = true);
          },
          onPageFinished: (url) async {
            debugPrint('✅ Page finished: $url');
            setState(() => _loading = false);

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
      });
    }
  }

  void _openInChrome() async {
    String url = widget.url;
    if (_isUniven) {
      url = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view';
    }

    try {
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(
          Uri.parse(url),
          mode: LaunchMode.externalApplication,
        );
        debugPrint('✅ Opened in Chrome: $url');
      }
    } catch (e) {
      debugPrint('❌ Error opening Chrome: $e');
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
              ...steps.map((step) => Padding(
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
                  )),
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
            onPressed: _showGuidanceDialog,
            tooltip: 'Application Guide',
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
          if (_loading)
            const Center(
              child: CircularProgressIndicator(),
            ),
        ],
      ),
    );
  }
}
