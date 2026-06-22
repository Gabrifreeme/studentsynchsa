import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;
import 'package:studentsyncsa/services/profile_validator.dart';

class AppWebView extends StatefulWidget {
  final String url;
  final String universityName;
  const AppWebView({super.key, required this.url, required this.universityName});

  @override
  State<AppWebView> createState() => _AppWebViewState();
}

enum AutofillStatus { idle, running, done, timeout, error }

class _AppWebViewState extends State<AppWebView> with SingleTickerProviderStateMixin {
  late final WebViewController _controller;
  String _profileJson = '{}';
  bool _loading = true;
  bool _showChat = false;
  AutofillStatus _autofillStatus = AutofillStatus.idle;
  StudentProfile? _profile;
  late AnimationController _animCtrl;
  late Animation<double> _slideUp;

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _slideUp = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOutCubic);

    _loadProfile();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) {
          setState(() => _loading = true);
        },
        onPageFinished: (_) async {
          setState(() => _loading = false);
          await _runPortalPatches();
          await _cleanupInjectedStar();
        },
      ))
      ..loadRequest(Uri.parse(widget.url));
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    final repo = ProfileRepositoryImpl();
    var profile = await repo.getProfile();
    if (profile == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      profile = await repo.getProfile();
    }
    if (profile == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      profile = await repo.getProfile();
    }
    if (profile != null && mounted) {
      _profile = profile;
      _profileJson = jsonEncode(profile.toJson());
    }
  }

  Future<void> _runAutofill() async {
    if (_profile != null) {
      final missing = ProfileValidator.missingFields(_profile!);
      if (missing.isNotEmpty) {
        _showAutofillSnackbar(
          'Complete your profile first: ${missing.join(', ')}',
        );
        return;
      }
    }

    if (!mounted) return;
    setState(() => _autofillStatus = AutofillStatus.running);

    try {
      await _controller
          .runJavaScript(star.buildAutofillOnlyScript(_profileJson))
          .timeout(const Duration(seconds: 8));
      if (!mounted) return;
      setState(() => _autofillStatus = AutofillStatus.done);
    } on TimeoutException {
      if (!mounted) return;
      setState(() => _autofillStatus = AutofillStatus.timeout);
      _showAutofillSnackbar('Autofill timed out — the portal may still be loading.');
    } catch (e) {
      if (!mounted) return;
      setState(() => _autofillStatus = AutofillStatus.error);
      _showAutofillSnackbar('Autofill failed: ${e.runtimeType}');
    }
  }

  void _showAutofillSnackbar(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), duration: const Duration(seconds: 4)),
    );
  }

  /// Run iEnabler portal patches in strict order (security → labels →
  /// autocomplete → focus → inputmode → form label) before any autofill.
  Future<void> _runPortalPatches() async {
    try {
      await _controller.runJavaScript(star.buildSecurityPatch());
      await _controller.runJavaScript(star.buildLabelPatch());
      await _controller.runJavaScript(star.buildAutocompletePatch());
      await _controller.runJavaScript(star.buildFocusPatch());
      await _controller.runJavaScript(star.buildInputmodePatch());
      await _controller.runJavaScript(star.buildFormLabelPatch());
    } catch (_) {
      // patches are optional — ignore failures on non-ITS pages
    }
  }

  Future<void> _cleanupInjectedStar() async {
    try {
      await _controller.runJavaScript(
        '''(function() {
          var remove = function(el) {
            if (!el || el.nodeType !== 1) return;
            var id = (el.id || '').toLowerCase();
            var title = (el.title || '').toLowerCase();
            var text = (el.textContent || '').toLowerCase();
            var style = window.getComputedStyle(el);
            if (id === 'ssa-star' || title === 'ask star') {
              el.remove();
              return;
            }
            if (style.position === 'fixed' && (style.right === '24px' || style.right === '0px' || style.right === '16px') && (style.bottom === '24px' || style.bottom === '0px' || style.bottom === '16px')) {
              if (text.indexOf('star') !== -1 || text.indexOf('⭐') !== -1 || el.querySelector('svg') || el.querySelector('img')) {
                el.remove();
              }
            }
          };
          document.querySelectorAll('div,button,a,span').forEach(remove);
        })();'''
      );
    } catch (_) {
      // ignore cleanup failures
    }
  }

  void _dismissChat() {
    _animCtrl.reverse().then((_) {
      if (mounted) setState(() => _showChat = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: AppColors.surface,
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading)
            const Center(child: CircularProgressIndicator()),

          // ── Autofill loading overlay ──
          if (_autofillStatus == AutofillStatus.running)
            Positioned(
              left: 0,
              right: 0,
              top: 0,
              bottom: 0,
              child: Container(
                color: Colors.black26,
                child: const Center(
                  child: Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 12),
                          Text('Auto-filling form…',
                              style: TextStyle(fontSize: 14)),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),

          Positioned(
            right: 24,
            bottom: 24,
            child: Semantics(
              label: 'Auto-fill form',
              child: GestureDetector(
                onTap: _autofillStatus == AutofillStatus.running
                    ? null
                    : () {
                        if (!mounted) return;
                        setState(() => _showChat = true);
                        _animCtrl.forward();
                      },
                child: Tooltip(
                  message: 'Auto-fill this form with your profile',
                  child: Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F1624),
                      borderRadius: BorderRadius.circular(28),
                      border: Border.all(color: const Color(0xFF7C3AED), width: 2),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF7C3AED).withValues(alpha: 0.5),
                          blurRadius: 20,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    alignment: Alignment.center,
                    child: _autofillStatus == AutofillStatus.running
                        ? const SizedBox(
                            width: 24, height: 24,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5, color: Colors.white))
                        : const Text('⭐',
                            style: TextStyle(fontSize: 32, color: Color(0xFFFFD700))),
                  ),
                ),
              ),
            ),
          ),

          // ── Chat overlay ──
          if (_showChat)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: FadeTransition(
                opacity: _slideUp,
                child: SlideTransition(
                  position: Tween<Offset>(
                    begin: const Offset(0, 0.5),
                    end: Offset.zero,
                  ).animate(_slideUp),
                  child: GestureDetector(
                    onTap: () {},
                    child: SafeArea(
                      top: false,
                      child: Container(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
                        decoration: const BoxDecoration(
                          color: Color(0xFF0F1624),
                          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                        ),
                        child: SingleChildScrollView(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                width: 40,
                                height: 4,
                                decoration: BoxDecoration(
                                  color: Colors.white24,
                                  borderRadius: BorderRadius.circular(2),
                                ),
                              ),
                              const SizedBox(height: 16),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(
                                    child: Container(
                                      padding: const EdgeInsets.all(14),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF1E293B),
                                        borderRadius: const BorderRadius.only(
                                          topRight: Radius.circular(16),
                                          bottomLeft: Radius.circular(16),
                                          bottomRight: Radius.circular(16),
                                        ),
                                        border: Border.all(color: Colors.white12),
                                      ),
                                      child: const Text(
                                        'Do you want me to auto fill this page?',
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontSize: 15,
                                          height: 1.4,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              Row(
                                children: [
                                  Expanded(
                                    child: SizedBox(
                                      height: 46,
                                      child: ElevatedButton(
                                        onPressed: () {
                                          _dismissChat();
                                          _runAutofill();
                                        },
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: const Color(0xFF10B981),
                                          foregroundColor: Colors.white,
                                          shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(12),
                                          ),
                                          elevation: 0,
                                        ),
                                        child: const Text('Yes',
                                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: SizedBox(
                                      height: 46,
                                      child: OutlinedButton(
                                        onPressed: _dismissChat,
                                        style: OutlinedButton.styleFrom(
                                          foregroundColor: Colors.white70,
                                          side: const BorderSide(color: Colors.white24),
                                          shape: RoundedRectangleBorder(
                                            borderRadius: BorderRadius.circular(12),
                                          ),
                                        ),
                                        child: const Text('No',
                                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
