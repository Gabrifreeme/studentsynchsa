import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

class UniversityWebViewScreen extends ConsumerStatefulWidget {
  final String url;
  final String universityName;

  const UniversityWebViewScreen({
    super.key,
    required this.url,
    required this.universityName,
  });

  @override
  ConsumerState<UniversityWebViewScreen> createState() => _UniversityWebViewScreenState();
}

class _UniversityWebViewScreenState extends ConsumerState<UniversityWebViewScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  String _currentUrl = '';
  String? _profileJson;

  @override
  void initState() {
    super.initState();

    _loadProfile();

    WebViewCookieManager().clearCookies();

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(true)
      ..setUserAgent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      )
      ..addJavaScriptChannel('AutofillResult', onMessageReceived: (msg) {
        try {
          final data = jsonDecode(msg.message);
          if (data['diag'] != null) {
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('DIAG: ${data['diag']}'),
                  duration: const Duration(seconds: 12),
                  backgroundColor: Colors.blue,
                ),
              );
            }
            return;
          }
          final filled = data['filled'] as int;
          final total = data['total'] as int;
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  '$filled of $total fields filled. Complete the reCAPTCHA, then tap "Open in Chrome" to submit.',
                ),
                duration: const Duration(seconds: 5),
                backgroundColor: Colors.green,
              ),
            );
          }
        } catch (_) {}
      });

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
          onPageFinished: (url) async {
            _currentUrl = url;
            setState(() => _loading = false);
            if (_profileJson != null) {
              try {
                await _controller.runJavaScript(star.buildAutofillOnlyScript(_profileJson!));
                await Future.delayed(const Duration(milliseconds: 30));
                await _controller.runJavaScript('window.requestFlutterAutofill();');
                debugPrint('✅ Autofill injected on page load');
              } catch (e) {
                debugPrint('❌ Autofill injection error: $e');
              }
            }
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
      return 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view';
    }
    return widget.url;
  }

  void _openInChrome() async {
    final uri = Uri.parse(_resolveUrl());
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('❌ launchUrl failed: $e');
    }
  }

  void _loadProfile() {
    final profile = ref.read(profileProvider).valueOrNull;
    if (profile != null) {
      _profileJson = jsonEncode(profile.toJson());
    }
  }

  Future<void> _injectAutofill(BuildContext dialogContext) async {
    if (_profileJson == null) {
      _loadProfile();
    }
    if (_profileJson != null) {
      Navigator.pop(dialogContext);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Attempting to autofill form...'), duration: Duration(seconds: 2)),
        );
      }
      try {
        await _controller.runJavaScript(star.buildAutofillOnlyScript(_profileJson!));
        await Future.delayed(const Duration(milliseconds: 30));
        await _controller.runJavaScript('window.requestFlutterAutofill();');
        debugPrint('✅ Autofill script injected');
      } catch (e) {
        debugPrint('❌ Autofill injection failed: $e');
      }
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No profile found. Complete your profile first.')),
        );
      }
    }
  }

  ({String title, List<(String, String)> steps}) _guidanceForPage(String url) {
    final u = url.toLowerCase();

    if (widget.universityName.toUpperCase() == 'UNIVEN' || widget.universityName.toUpperCase() == 'VENDA') {
      return (
        title: 'Venda Application Guide',
        steps: [
          ('', 'This steps are very easy, if you are a new student then you do not have a student number, tap on "Please select" and pick NO, if you are returning to complete an application form pick YES but if you new then it is NO'),
          ('', 'next if you have a Qualification Specific Token pick YES, but when you new, you don\'t have then it will be NO again.'),
          ('', 'That\'s it just do your consent to Venda university by tapping yes and next, If you like to read the POPI Clause first follow this link: https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view'),
        ],
      );
    }

    if (u.contains('gw1view') || u.contains('oap') || u.contains('biographical') || u.contains('nok')) {
      return (
        title: '📋 Application Process',
        steps: [
          ('1', 'Fill Next of Kin name, mobile, home & work phone'),
          ('2', 'Enter Next of Kin postal address lines 1-4 and code'),
          ('3', 'Enter Next of Kin email address'),
          ('4', 'Fill Account Contact name, mobile & home phone'),
          ('5', 'Enter Account Contact postal address lines 1-4 and code'),
          ('6', 'Enter Account Contact email address'),
        ],
      );
    }

    if (u.contains('id') || u.contains('persona') || u.contains('idnum') || u.contains('nationality') || u.contains('biographical')) {
      return (
        title: '🆔 Biographical Details',
        steps: [
          ('1', 'Select SA Citizen status'),
          ('2', 'Enter Citizenship Code'),
          ('3', 'Select Gender, Date of Birth (DD-MON-YYYY), Title'),
          ('4', 'Enter Initials, Surname, First Names'),
          ('5', 'Maiden name (optional)'),
          ('6', 'Select Marital Status, Home Language, Ethnic Group'),
          ('7', 'Select Employed? and Bursary required?'),
          ('8', 'Where did you hear about us?'),
          ('9', 'Street Address Line 1-4, Postal Code'),
          ('10', 'Tick if Postal Address differs from Street'),
          ('11', 'SA Cell Phone Number?'),
          ('12', 'Work Telephone, Home Telephone'),
          ('13', 'Email and Verify email'),
          ('14', 'Apply for residence?'),
          ('15', 'Disability or impairment?'),
        ],
      );
    }

    if (u.contains('contact') || u.contains('addr') || u.contains('phone')) {
      return (
        title: '📞 Address & Contact',
        steps: [
          ('1', 'Enter Street Address lines 1-4 and Postal Code'),
          ('2', 'Tick if Postal Address is different from Street'),
          ('3', 'Enter Email and Verify email'),
          ('4', 'Enter Home Telephone and Work Telephone'),
          ('5', 'Select Residence and Disability preferences'),
        ],
      );
    }

    if (u.contains('academic') || u.contains('subject') || u.contains('grade') || u.contains('qual') || u.contains('matric') || u.contains('result')) {
      return (
        title: '📚 Results Details',
        steps: [
          ('1', 'Enter Matric/Grade 12 Year'),
          ('2', 'Select Undergraduate or Postgraduate'),
          ('3', 'Select Upgrading and Matric type (SA/International)'),
          ('4', 'Enter Examination Number and School Leaving Certificate'),
          ('5', 'Add Subject: select subject, grade, result, symbol'),
          ('6', 'Click "Add Subject" for each additional subject'),
        ],
      );
    }

    if (u.contains('school') || u.contains('previous') || u.contains('institution') || u.contains('tertiary')) {
      return (
        title: '🏫 Previous Studies',
        steps: [
          ('1', 'Select which school you attended last'),
          ('2', 'Select what you are currently doing'),
          ('3', 'Select if you studied at another institution'),
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
      title: 'Application Guide',
      steps: [
        ('1', 'Fill Next of Kin & Account Contact details'),
        ('2', 'Enter Biographical details and ID'),
        ('3', 'Enter Address, Contact, Residence info'),
        ('4', 'Fill Matric/Results and Subject details'),
        ('5', 'Enter Previous School/Tertiary information'),
        ('6', 'Review all information carefully'),
        ('7', 'Submit & SAVE your student number!'),
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
            const StarAvatar(size: 28),
            const SizedBox(width: 8),
            Flexible(child: Text(guidance.title, style: const TextStyle(fontSize: 16))),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ...guidance.steps.map((s) => _GuideStep(s.$1, s.$2)),
            if (_profileJson != null) ...[
              const SizedBox(height: 12),
              const Text('You like me to try and auto fill this page?',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _injectAutofill(ctx),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.green),
                        foregroundColor: Colors.green,
                      ),
                      child: const Text('Yes'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(ctx),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.grey),
                        foregroundColor: Colors.grey,
                      ),
                      child: const Text('No'),
                    ),
                  ),
                ],
              ),
            ],
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
