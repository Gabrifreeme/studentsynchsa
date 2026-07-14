import 'dart:async';

import 'package:universal_html/html.dart' as html;

Future<String?> pickFile([String accept = '']) {
  final completer = Completer<String?>();
  final input = html.FileUploadInputElement()..accept = accept;
  input.click();
  input.onChange.listen((_) {
    if (input.files!.isNotEmpty) {
      completer.complete(input.files![0].name ?? '');
    } else {
      completer.complete(null);
    }
  });
  return completer.future;
}
