import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/presentation/screens/universities/webview_impl.dart'
    if (dart.library.html)
    'package:studentsyncsa/presentation/screens/universities/webview_web_fallback.dart';
import 'package:url_launcher/url_launcher.dart';

/// Bursary applications use the same in-app WebView + Star auto-fill as the
/// university portals. On web builds WebView is unavailable, so we offer the
/// external portal link instead (auto-fill is mobile-only by design).
class FundingWebViewScreen extends StatelessWidget {
  final String url;
  final String name;

  const FundingWebViewScreen({
    super.key,
    required this.url,
    required this.name,
  });

  @override
  Widget build(BuildContext context) {
    if (kIsWeb) {
      return Scaffold(
        appBar: AppBar(title: Text(name)),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(17),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Open application portal in a new tab',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 10)),
                const SizedBox(height: 14),
                FilledButton.icon(
                  onPressed: () async {
                    final uri = Uri.parse(url);
                    if (await canLaunchUrl(uri)) {
                      await launchUrl(uri, mode: LaunchMode.externalApplication);
                    }
                  },
                  icon: const StarIcon(Icons.open_in_new, size: 16),
                  label: const Text('Open Portal'),
                  style: FilledButton.styleFrom(
                      backgroundColor: AppColors.primary),
                ),
              ],
            ),
          ),
        ),
      );
    }
    return AppWebView(url: url, universityName: name);
  }
}
