import io, os

# ============================================================
# 1. Web implementation
# ============================================================
web_impl = """import 'dart:convert';
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
"""

# ============================================================
# 2. IO (mobile/desktop) implementation
# ============================================================
io_impl = """import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:url_launcher/url_launcher.dart';

Future<void> saveFileOnPlatform(List<int> bytes, String fileName, String mimeType) async {
  final dir = await getTemporaryDirectory();
  final file = File('${dir.path}/$fileName');
  await file.writeAsBytes(bytes);
  final uri = Uri.file(file.path);
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}
"""

# ============================================================
# 3. Conditionally imported barrel (this is the trick)
# ============================================================
barrel = """export 'file_saver_io.dart' if (dart.library.html) 'file_saver_web.dart';
"""

os.makedirs(r"C:\Users\chris\LipSyncStudent\lib\services", exist_ok=True)

with io.open(r"C:\Users\chris\LipSyncStudent\lib\services\file_saver_web.dart", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(web_impl)
print("CREATED: file_saver_web.dart")

with io.open(r"C:\Users\chris\LipSyncStudent\lib\services\file_saver_io.dart", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(io_impl)
print("CREATED: file_saver_io.dart")

with io.open(r"C:\Users\chris\LipSyncStudent\lib\services\file_saver.dart", "w", encoding="utf-8", newline="\r\n") as f:
    f.write(barrel)
print("CREATED: file_saver.dart (barrel)")

# ============================================================
# 4. Patch room_chat_screen.dart to use the helper
# ============================================================
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# Add import for the helper
if "file_saver.dart" not in content:
    content = content.replace(
        "import 'package:lipsyncstudent/data/models/chat_message.dart';",
        "import 'package:lipsyncstudent/data/models/chat_message.dart';\r\nimport 'package:lipsyncstudent/services/file_saver.dart';",
        1
    )
    print("PATCHED: added file_saver import")

# Replace the old launchUrl logic with the helper
old_block = """                                              onTap: () async {
                                                if (m.fileData == null) {
                                                  if (!context.mounted) return;
                                                  ScaffoldMessenger.of(context).showSnackBar(
                                                    const SnackBar(content: Text('File data not stored'), backgroundColor: AppColors.error),
                                                  );
                                                  return;
                                                }
                                                final bytes = base64Decode(m.fileData!);
                                                final uri = Uri.dataFromBytes(bytes, mimeType: m.mimeType ?? 'application/octet-stream');
                                                await launchUrl(uri, mode: LaunchMode.externalApplication);
                                              },"""

new_block = """                                              onTap: () async {
                                                if (m.fileData == null) {
                                                  if (!context.mounted) return;
                                                  ScaffoldMessenger.of(context).showSnackBar(
                                                    const SnackBar(content: Text('File data not stored'), backgroundColor: AppColors.error),
                                                  );
                                                  return;
                                                }
                                                final bytes = base64Decode(m.fileData!);
                                                final fileName = m.text.replaceFirst('[FILE] ', '');
                                                final mime = m.mimeType ?? 'application/octet-stream';
                                                await saveFileOnPlatform(bytes, fileName, mime);
                                              },"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print("PATCHED: download handler uses saveFileOnPlatform")
else:
    print("WARNING: download handler pattern not found")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE")
