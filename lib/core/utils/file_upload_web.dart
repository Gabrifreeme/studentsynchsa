import 'dart:html' as html;
import 'dart:async';

Future<String?> pickFile([String accept = '']) {
  final completer = Completer<String?>();
  final input = html.FileUploadInputElement()..accept = accept;
  input.click();
  input.onChange.listen((_) {
    if (input.files!.isNotEmpty) {
      completer.complete(input.files![0]!.name ?? '');
    } else {
      completer.complete(null);
    }
  });
  return completer.future;
}
