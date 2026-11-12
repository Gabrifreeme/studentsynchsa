import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';

Future<void> saveFileOnPlatform(List<int> bytes, String fileName, String mimeType) async {
  final dir = await getTemporaryDirectory();
  final file = File('${dir.path}/$fileName');
  await file.writeAsBytes(bytes);
  final uri = Uri.file(file.path);
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}
