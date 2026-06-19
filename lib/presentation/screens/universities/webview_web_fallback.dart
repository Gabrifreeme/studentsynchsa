import 'package:flutter/material.dart';

// Stub for web platform — MobileWebView is never actually used on web
class AppWebView extends StatelessWidget {
  final String url;
  final String universityName;
  const AppWebView({super.key, required this.url, required this.universityName});

  @override
  Widget build(BuildContext context) {
    throw UnsupportedError('AppWebView is not supported on web');
  }
}
