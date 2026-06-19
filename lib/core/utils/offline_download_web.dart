import 'dart:async';
import 'dart:html' as html;
import 'package:flutter/services.dart';

Future<void> downloadAsset(String assetPath) async {
  try {
    final data = await rootBundle.load(assetPath);
    final blob = html.Blob(<dynamic>[data.buffer.asUint8List()]);
    final url = html.Url.createObjectUrlFromBlob(blob);
    final anchor = html.AnchorElement(href: url)
      ..setAttribute('download', assetPath.split('/').last)
      ..style.display = 'none';
    html.document.body!.append(anchor);
    anchor.click();
    anchor.remove();
    html.Url.revokeObjectUrl(url);
  } catch (e) {
    // Fallback: try direct URL
    final url = '/${assetPath.startsWith('/') ? assetPath.substring(1) : assetPath}';
    final anchor = html.AnchorElement(href: url)
      ..setAttribute('download', assetPath.split('/').last)
      ..style.display = 'none';
    html.document.body!.append(anchor);
    anchor.click();
    anchor.remove();
  }
}
