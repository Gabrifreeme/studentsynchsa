import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

class AppWebView extends StatefulWidget {
  final String url;
  final String universityName;
  final StudentProfile? profile;

  const AppWebView({
    super.key,
    required this.url,
    required this.universityName,
    this.profile,
  });

  @override
  State<AppWebView> createState() => _AppWebViewState();
}

class _AppWebViewState extends State<AppWebView> {
  late final WebViewController _controller;
  bool _loading = true;
  StudentProfile? _profile;
  bool _isUniven = false;
  int _loadCount = 0;

  String? _profileJson;

  @override
  void initState() {
    super.initState();
    _profile = widget.profile;
    _isUniven = widget.universityName.toUpperCase() == 'UNIVEN';
    _loadProfileIfMissing();

    WebViewCookieManager().clearCookies();

    if (_profile != null) {
      _profileJson = jsonEncode(_profile!.toJson());
    }

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(true)
      ..setUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      )
      ..addJavaScriptChannel(
        'FlutterNavigation',
        onMessageReceived: (JavaScriptMessage message) {
          final targetUrl = message.message;
          debugPrint("🔴 JavaScript navigation: $targetUrl");
          if (targetUrl.startsWith('http') && mounted) {
            _controller.loadRequest(Uri.parse(targetUrl));
          }
        },
      )
      ..addJavaScriptChannel(
        'FlutterLog',
        onMessageReceived: (JavaScriptMessage message) {
          debugPrint("🟢 JS: ${message.message}");
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
            debugPrint("🟡 NAVIGATION: $url");

            if (url.contains('univenierp01') || url.contains('gw1pkg')) {
              debugPrint("🎯 ITS PORTAL DETECTED!");
            }

            return NavigationDecision.navigate;
          },
          onPageStarted: (url) {
            debugPrint("📄 Page started: $url");
            setState(() => _loading = true);
          },
          onPageFinished: (url) async {
            debugPrint("✅ Page finished: $url");
            setState(() => _loading = false);

            _loadCount++;
            debugPrint("📊 Page load #$_loadCount");

            await _injectAllScripts(url);
          },
          onWebResourceError: (error) {
            debugPrint("🔴 ERROR: ${error.description}");
          },
          onProgress: (progress) {
            if (progress == 100) {
              debugPrint("✅ Loaded 100%");
            }
          },
        ),
      )
      ..loadRequest(Uri.parse(_getInitialUrl()));
  }

  Future<void> _injectAllScripts(String currentUrl) async {
    debugPrint("💉 Injecting scripts on: $currentUrl");

    try {
      await _controller.runJavaScript(star.buildNavigationFixScript());
      debugPrint("✅ Navigation fix injected");

      await _runPortalPatches();
      debugPrint("✅ Portal patches injected");

      if (_profileJson != null) {
        await _controller.runJavaScript(star.buildAutofillScript(_profileJson!));
        await Future.delayed(const Duration(milliseconds: 30));
        await _controller.runJavaScript('window.requestFlutterAutofill();');
        debugPrint("✅ Autofill script injected");
      }

      if (_isUniven) {
        await _controller.runJavaScript('''
          (function() {
            if (document.getElementById('flutter-star-btn')) return;

            var star = document.createElement('div');
            star.id = 'flutter-star-btn';
            star.innerHTML = '⭐';
            star.style.position = 'fixed';
            star.style.bottom = '20px';
            star.style.right = '20px';
            star.style.width = '60px';
            star.style.height = '60px';
            star.style.borderRadius = '50%';
            star.style.backgroundColor = '#FFD700';
            star.style.color = '#000';
            star.style.fontSize = '30px';
            star.style.display = 'flex';
            star.style.alignItems = 'center';
            star.style.justifyContent = 'center';
            star.style.zIndex = '99999';
            star.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
            star.style.cursor = 'pointer';
            star.style.border = '3px solid #000';

            star.onclick = function() {
              console.log('⭐ Star clicked on ITS portal');
              var inputs = document.querySelectorAll('input, select, textarea');
              for (var input of inputs) {
                if (input.name && input.name.toLowerCase().includes('name')) {
                  input.value = '${_profile?.personal.firstName ?? ''} ${_profile?.personal.lastName ?? ''}';
                }
                if (input.name && input.name.toLowerCase().includes('email')) {
                  input.value = '${_profile?.contact.email ?? ''}';
                }
                if (input.name && input.name.toLowerCase().includes('id')) {
                  input.value = '${_profile?.personal.idNumber ?? ''}';
                }
              }
              var event = new Event('change', { bubbles: true });
              for (var input of inputs) {
                input.dispatchEvent(event);
              }
              console.log('⭐ Form fields filled!');
            };

            document.body.appendChild(star);
            console.log('⭐ Star button added to ITS portal');
          })();
        ''');
        debugPrint("✅ Star button injected on ITS portal");
      }

      debugPrint("✅ All scripts injected successfully on: $currentUrl");

    } catch (e) {
      debugPrint("❌ Injection error: $e");
    }
  }

  String _getInitialUrl() {
    if (_isUniven) {
      return "https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?x_processcode=ITS_OAP";
    }
    return widget.url;
  }

  Future<void> _runPortalPatches() async {
    try {
      await _controller.runJavaScript(star.buildViewportPatch());
      await _controller.runJavaScript(
        "var style = document.createElement('style'); style.innerHTML = '* { font-size: 16px !important; } input, select, textarea { font-size: 16px !important; }'; document.head.appendChild(style);",
      );
      await _controller.runJavaScript(star.buildBlanketAutofillSuppressScript());
      await _controller.runJavaScript(star.buildSecurityPatch());
      await _controller.runJavaScript(star.buildLabelPatch());
      await _controller.runJavaScript(star.buildAutocompletePatch());
      await _controller.runJavaScript(star.buildSelectAutocompletePatch());
      await _controller.runJavaScript(star.buildProvinceDisambiguationPatch());
      await _controller.runJavaScript(star.buildFocusPatch());
      await _controller.runJavaScript(star.buildInputmodePatch());
      await _controller.runJavaScript(star.buildFormLabelPatch());
    } catch (_) {}
  }

  Future<void> _loadProfileIfMissing() async {
    if (_profile != null) {
      _profileJson = jsonEncode(_profile!.toJson());
      return;
    }

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
      final profile = p;
      setState(() {
        _profile = profile;
        _profileJson = jsonEncode(profile.toJson());
      });
    }
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
