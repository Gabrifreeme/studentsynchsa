import 'dart:html' as html;

void downloadAsset(String assetPath) {
  final url = assetPath.startsWith('/') ? assetPath : '/$assetPath';
  final anchor = html.AnchorElement(href: url)
    ..setAttribute('download', assetPath.split('/').last)
    ..style.display = 'none';
  html.document.body!.append(anchor);
  anchor.click();
  anchor.remove();
}
