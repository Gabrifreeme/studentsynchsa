// ignore_for_file: deprecated_member_use, avoid_web_libraries_in_flutter

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
    final url = _webAssetUrl(assetPath);
    final anchor = html.AnchorElement(href: url)
      ..setAttribute('download', assetPath.split('/').last)
      ..style.display = 'none';
    html.document.body!.append(anchor);
    anchor.click();
    anchor.remove();
  }
}

String _webAssetUrl(String assetPath) {
  final clean =
      assetPath.startsWith('/') ? assetPath.substring(1) : assetPath;
  // Flutter serves declared assets under the web root's /assets/ folder.
  return '/assets/$clean';
}

Future<void> openAsset(String assetPath) async {
  html.window.open(_webAssetUrl(assetPath), '_blank');
}
