import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/universities/webview_impl.dart'
    if (dart.library.html) 'package:studentsyncsa/presentation/screens/universities/webview_web_fallback.dart';
import 'package:url_launcher/url_launcher.dart';

class UniversityWebViewScreen extends StatelessWidget {
  final String url;
  final String universityName;
  const UniversityWebViewScreen({
    super.key,
    required this.url,
    required this.universityName,
  });

  @override
  Widget build(BuildContext context) {
    if (kIsWeb) {
      return Scaffold(
        appBar: AppBar(title: Text(universityName)),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Open application portal in a new tab',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 15)),
                const SizedBox(height: 20),
                FilledButton.icon(
                  onPressed: () async {
                    final uri = Uri.parse(url);
                    if (await canLaunchUrl(uri)) {
                      await launchUrl(uri, mode: LaunchMode.externalApplication);
                    }
                  },
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Open Portal'),
                  style: FilledButton.styleFrom(backgroundColor: AppColors.primary),
                ),
              ],
            ),
          ),
        ),
      );
    }
    return AppWebView(url: url, universityName: universityName);
  }
}
