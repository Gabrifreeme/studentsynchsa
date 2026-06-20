import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

class AppWebView extends StatefulWidget {
  final String url;
  final String universityName;
  const AppWebView({super.key, required this.url, required this.universityName});

  @override
  State<AppWebView> createState() => _AppWebViewState();
}

class _AppWebViewState extends State<AppWebView> {
  late final WebViewController _controller;
  String _profileJson = '{}';
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) {
          setState(() => _loading = true);
        },
        onPageFinished: (_) async {
          setState(() => _loading = false);
          await _injectStar();
        },
      ))
      ..loadRequest(Uri.parse(widget.url));
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
      _profileJson = jsonEncode(profile.toJson());
    }
  }

  Future<void> _injectStar() async {
    if (_profileJson == '{}') {
      await _loadProfile();
    }
    try {
      await _controller.runJavaScript(star.buildAutofillScript(_profileJson));
    } catch (e) {
      debugPrint('Star injection failed: $e');
    }
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
        ],
      ),
    );
  }
}
