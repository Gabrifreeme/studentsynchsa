import 'dart:async';
import 'dart:convert';
import 'dart:html';

class AiService {
  static Future<void> warmUp() async {}

  static Future<void> askStream({
    required String prompt,
    required void Function(String token) onToken,
  }) async {
    try {
      final url = 'http://127.0.0.1:11434/api/generate';
      final body = jsonEncode({
        'model': 'qwen3:0.6b',
        'prompt': prompt,
        'stream': true,
      });

      final request = HttpRequest();
      request.open('POST', url, async: true);
      request.setRequestHeader('Content-Type', 'application/json');

      final completer = Completer<void>();

      request.onProgress.listen((_) {
        if (request.readyState < 2) return;
        final text = request.responseText;
        if (text == null || text.isEmpty) return;
        final lines = text.split('\n');
        for (final line in lines) {
          if (line.trim().isEmpty) continue;
          try {
            final data = jsonDecode(line);
            final token = data['response'] as String?;
            if (token != null && token.isNotEmpty) {
              onToken(token);
            }
          } catch (_) {}
        }
      });

      request.onLoadEnd.listen((_) {
        if (!completer.isCompleted) completer.complete();
      });

      request.onError.listen((e) {
        if (!completer.isCompleted) completer.completeError(e);
      });

      request.send(body);

      await completer.future.timeout(const Duration(seconds: 90));
    } catch (e) {
      onToken('Star AI error: $e');
    }
  }

  static Future<String> ask(String prompt) async {
    final buffer = StringBuffer();
    await askStream(
      prompt: prompt,
      onToken: (token) => buffer.write(token),
    );
    return buffer.toString();
  }

  static String buildPrompt({
    required String firstName,
    required int apsScore,
    required List<String> subjects,
    required List<String> careerInterests,
    String? province,
    bool needsFunding = false,
  }) {
    return '''Hello $firstName! Based on your profile:
- APS Score: $apsScore
- Subjects: ${subjects.join(', ')}
- Career Interests: ${careerInterests.join(', ')}
- Province: ${province ?? 'Not specified'}
- Needs Funding: $needsFunding

What would you like to know about university applications or career options?''';
  }
}
