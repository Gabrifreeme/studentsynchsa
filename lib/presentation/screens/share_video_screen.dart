import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Renders a Facebook video share link of the form:
///   https://www.facebook.com/share/v/<videoId>/
/// by embedding Facebook's video plugin for that share URL.
///
/// Route shape (see app_router.dart):
///   /share/v/:videoId
class ShareVideoScreen extends StatefulWidget {
  const ShareVideoScreen({super.key, required this.videoId});

  final String videoId;

  /// The canonical Facebook share/v URL this screen is rendering.
  String get shareUrl => 'https://www.facebook.com/share/v/$videoId/';

  @override
  State<ShareVideoScreen> createState() => _ShareVideoScreenState();
}

class _ShareVideoScreenState extends State<ShareVideoScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  String _title = 'Shared Video';

  @override
  void initState() {
    super.initState();
    // The ID we receive may already be decoded by go_router; the share URL is
    // a stable identifier we can present to the user.
    _title = widget.videoId;
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (url) {
            setState(() => _isLoading = false);
          },
        ),
      )
      ..loadRequest(Uri.parse(_embedUrl()))
      ..setBackgroundColor(Colors.transparent);
  }

  String _embedUrl() {
    final href = widget.shareUrl;
    // Encode the full share URL as the `href` query param for Facebook's
    // embedded video plugin. This renders the share/v video inline.
    final encoded = Uri.encodeComponent(href);
    return 'https://www.facebook.com/plugins/video.php?'
        'href=$encoded'
        '&amp;show_text=0'
        '&amp;width=500'
        '&amp;height=500'
        '&amp;autoplay=false'
        '&amp;appId'
        '&amp;locale=en_US';
  }

  void _copyShareLink() {
    Clipboard.setData(ClipboardData(text: widget.shareUrl));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Share link copied to clipboard')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_title, overflow: TextOverflow.ellipsis),
        actions: [
          IconButton(
            icon: const Icon(Icons.content_copy),
            onPressed: _copyShareLink,
            tooltip: 'Copy share link',
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_isLoading) const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
