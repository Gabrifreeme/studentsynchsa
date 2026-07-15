import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class UniversityWebViewScreen extends StatefulWidget {
  final String url;
  final String universityName;

  const UniversityWebViewScreen({
    super.key,
    required this.url,
    required this.universityName,
  });

  @override
  State<UniversityWebViewScreen> createState() => _UniversityWebViewScreenState();
}

class _UniversityWebViewScreenState extends State<UniversityWebViewScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  String _currentUrl = '';

  @override
  void initState() {
    super.initState();

    WebViewCookieManager().clearCookies();

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(true)
      ..setUserAgent(
        'Mozilla/5.0 (Linux; Android 15; HONOR ABR-NX1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36',
      );

    if (_controller.platform is AndroidWebViewController) {
      (_controller.platform as AndroidWebViewController).setTextZoom(150);
    }

    _controller
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (url) {
            _currentUrl = url;
            setState(() => _loading = true);
          },
          onPageFinished: (url) {
            _currentUrl = url;
            setState(() => _loading = false);
          },
          onWebResourceError: (err) => debugPrint('❌ WebView: ${err.description}'),
          onSslAuthError: (error) => error.proceed(),
        ),
      );

    _loadPortal();
  }

  Future<void> _loadPortal() async {
    await _controller.loadRequest(Uri.parse(_resolveUrl()));
  }

  String _resolveUrl() {
    final name = widget.universityName.toUpperCase();
    if (name == 'UNIVEN' || name == 'VENDA') {
      return 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP';
    }
    return widget.url;
  }

  void _openInChrome() async {
    final uri = Uri.parse(_resolveUrl());
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  ({String title, List<(String, String)> steps}) _guidanceForPage(String url) {
    final u = url.toLowerCase();

    if (u.contains('gw1view') || u.contains('oap')) {
      return (
        title: '📋 Applications Home',
        steps: [
          ('1', 'Look for the red "APPLY" or "New Application" button'),
          ('2', 'Click it to start a new application'),
          ('3', 'Select the program you want to apply for'),
          ('4', 'Read the instructions on the next page'),
        ],
      );
    }

    if (u.contains('id') || u.contains('persona') || u.contains('idnum')) {
      return (
        title: '🆔 ID & Personal Details',
        steps: [
          ('1', 'Enter your South African ID number (13 digits)'),
          ('2', 'Enter your full name as on ID document'),
          ('3', 'Select your date of birth'),
          ('4', 'Select your gender'),
          ('5', 'Double-check ID number before proceeding'),
        ],
      );
    }

    if (u.contains('contact') || u.contains('addr') || u.contains('phone')) {
      return (
        title: '📞 Contact Information',
        steps: [
          ('1', 'Enter your cellphone number'),
          ('2', 'Enter your email address'),
          ('3', 'Enter your postal address'),
          ('4', 'Enter your residential address'),
          ('5', 'Add an alternative contact number'),
        ],
      );
    }

    if (u.contains('academic') || u.contains('subject') || u.contains('grade') || u.contains('qual')) {
      return (
        title: '📚 Academic History',
        steps: [
          ('1', 'Select your matric year'),
          ('2', 'Enter your subjects and symbols'),
          ('3', 'Add any tertiary qualifications if applicable'),
          ('4', 'Verify all marks are correct'),
        ],
      );
    }

    if (u.contains('doc') || u.contains('upload') || u.contains('file')) {
      return (
        title: '📎 Document Upload',
        steps: [
          ('1', 'Upload certified ID copy'),
          ('2', 'Upload matric results / academic record'),
          ('3', 'Upload proof of residence'),
          ('4', 'Upload any additional documents requested'),
          ('5', 'Make sure files are clear and under 2MB'),
        ],
      );
    }

    if (u.contains('review') || u.contains('confirm') || u.contains('submit')) {
      return (
        title: '✅ Review & Submit',
        steps: [
          ('1', 'Read through all your details carefully'),
          ('2', 'Check ID number and contact info'),
          ('3', 'Check subject choices and symbols'),
          ('4', 'Scroll to the bottom and click SUBMIT'),
          ('5', '⚠️ SAVE YOUR STUDENT NUMBER after submission!'),
        ],
      );
    }

    return (
      title: '⭐ Application Guide',
      steps: [
        ('1', 'Click "Apply Now" or the red APPLY button'),
        ('2', 'Enter your South African ID number'),
        ('3', 'Fill in your personal details'),
        ('4', 'Enter your contact information'),
        ('5', 'Provide your academic history'),
        ('6', 'Upload required documents'),
        ('7', 'Review all information carefully'),
        ('8', 'Submit & SAVE your student number!'),
      ],
    );
  }

  void _showGuidance() {
    final guidance = _guidanceForPage(_currentUrl);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: [
            const Text('⭐', style: TextStyle(fontSize: 28)),
            const SizedBox(width: 8),
            Flexible(child: Text(guidance.title, style: const TextStyle(fontSize: 16))),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ...guidance.steps.map((s) => _GuideStep(s.$1, s.$2)),
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
                      '⚠️ SAVE your student number after submission!',
                      style: TextStyle(fontSize: 12, color: Colors.red),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
          ElevatedButton.icon(
            onPressed: () { Navigator.pop(ctx); _openInChrome(); },
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
          GestureDetector(
            onTap: _showGuidance,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: StarAvatar(size: 30, pulse: true),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.open_in_browser),
            onPressed: _openInChrome,
            tooltip: 'Open in Chrome',
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
            const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}

class _GuideStep extends StatelessWidget {
  final String number;
  final String text;
  const _GuideStep(this.number, this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$number.', style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(width: 6),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 13))),
        ],
      ),
    );
  }
}
