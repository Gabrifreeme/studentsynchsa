import 'dart:io';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:lipsyncstudent/services/autofill_script.dart' as star;

class UniversityWebViewScreen extends StatefulWidget {
  // Changed 'initialUrl' to 'url' to match your app_router.dart
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
  late WebViewController _controller;
  bool _loading = true;
  String? _currentUrl;
  String? _profileJson;

  @override
  void initState() {
    super.initState();
    _profileJson = widget.profileJson;
    _currentUrl = widget.url; // Use the 'url' from the widget

    _controller = WebViewController();

    // 1. Android Specific Settings (Cookies & Media)
        // 1. Android Specific Settings (Cookies & Media)
    if (Platform.isAndroid) {
      final androidController = _controller.platform as AndroidWebViewController;
      androidController.setMediaPlaybackRequiresUserGesture(false);
      
      // FIXED: Correct class and constructor for webview_flutter 4.14.1
      final cookieManager = AndroidWebViewCookieManager(
        const PlatformWebViewCookieManagerCreationParams(),
      );
      cookieManager.setAcceptThirdPartyCookies(androidController, true);
    }
    // 2. Set JS & User-Agent
    _controller
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

    // 3. Navigation & WAF Bypass Setup
    _controller.setNavigationDelegate(
      NavigationDelegate(
        onPageStarted: (url) {
          // WAF BYPASS: Catch Oracle deep links and redirect to the safe page
          if (url.contains('univenierp01') || url.contains('gw1view') || url.contains('prodi41')) {
            _controller.loadRequest(
              Uri.parse('https://www.univen.ac.za/apply/'),
            );
            return;
          }

          _currentUrl = url;
          setState(() => _loading = true);
        },
        onPageFinished: (url) async {
          _currentUrl = url;
          setState(() => _loading = false);

          // Re-inject the Apply button interceptor
          try {
            final navScript = star.buildNavigationFixScript();
            await _controller.runJavaScript(navScript);
          } catch (e) {
            debugPrint('Nav script error: $e');
          }
          
          // Inject Autofill
          if (_profileJson != null) {
            try {
              final autofillScript = star.buildAutofillScript(_profileJson!);
              await _controller.runJavaScript(autofillScript);
            } catch (e) {
              debugPrint('Autofill error: $e');
            }
          }
        },
        onWebResourceError: (error) {
          debugPrint('WebView error: $error');
        },
      ),
    );

    // 4. Load the initial URL (Bypassing to UNIVEN apply page immediately)
    _controller.loadRequest(
      Uri.parse('https://www.univen.ac.za/apply/'),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: Colors.blue,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _controller.reload(),
          ),
          IconButton(
            icon: const Icon(Icons.home),
            onPressed: () {
              _controller.loadRequest(
                Uri.parse('https://www.univen.ac.za/apply/'),
              );
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