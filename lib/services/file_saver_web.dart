import 'dart:convert';
// ignore: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html' as html;

Future<void> saveFileOnPlatform(List<int> bytes, String fileName, String mimeType) async {
  final base64Data = base64Encode(bytes);
  final dataUrl = 'data:$mimeType;base64,$base64Data';
  final anchor = html.AnchorElement(href: dataUrl)
    ..setAttribute('download', fileName)
    ..style.display = 'none';
  html.document.body?.children.add(anchor);
  anchor.click();
  anchor.remove();
}
