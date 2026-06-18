import 'dart:async';
import 'dart:convert';
import 'dart:html' as html;

class AiService {
  static const _ollamaUrl = 'http://127.0.0.1:11434/api/generate';

  /// Pre-warm the model so first user request is faster.
  static Future<void> warmUp() async {
    try {
      final body = jsonEncode({
        'model': 'qwen3:0.6b',
        'prompt': 'Hello',
        'stream': false,
      });
      final request = html.HttpRequest();
      request.open('POST', _ollamaUrl, async: true);
      request.setRequestHeader('Content-Type', 'application/json');
      request.send(body);
      await request.onLoad.first.timeout(const Duration(seconds: 30));
    } catch (_) {}
  }

  /// Ask Star and stream the response token by token via [onToken].
  static Future<void> askStream({
    required String prompt,
    required void Function(String token) onToken,
  }) async {
    try {
      final body = jsonEncode({
        'model': 'qwen3:0.6b',
        'prompt': prompt,
        'stream': true,
      });
      final request = html.HttpRequest();
      request.open('POST', _ollamaUrl, async: true);
      request.setRequestHeader('Content-Type', 'application/json');
      request.responseType = 'text';

      var lastLength = 0;
      request.onProgress.listen((_) {
        final text = request.responseText ?? '';
        if (text.length > lastLength) {
          final chunk = text.substring(lastLength);
          lastLength = text.length;
          for (final line in chunk.split('\n')) {
            if (line.trim().isEmpty) continue;
            try {
              final data = jsonDecode(line);
              final token = data['response'] as String?;
              if (token != null && token.isNotEmpty) {
                onToken(token);
              }
            } catch (_) {}
          }
        }
      });

      request.send(body);
      await request.onLoad.first.timeout(const Duration(seconds: 90));
      final text = request.responseText ?? '';
      if (text.length > lastLength) {
        final chunk = text.substring(lastLength);
        for (final line in chunk.split('\n')) {
          if (line.trim().isEmpty) continue;
          try {
            final data = jsonDecode(line);
            final token = data['response'] as String?;
            if (token != null && token.isNotEmpty) {
              onToken(token);
            }
          } catch (_) {}
        }
      }
    } catch (e) {
      onToken('Star is offline — run "ollama serve" to wake me up! Error: $e');
    }
  }

  /// Non-streaming ask (kept for the initial recommendation button).
  static Future<String> ask(String prompt) async {
    try {
      final body = jsonEncode({
        'model': 'qwen3:0.6b',
        'prompt': prompt,
        'stream': false,
      });
      final request = html.HttpRequest();
      request.open('POST', _ollamaUrl, async: true);
      request.setRequestHeader('Content-Type', 'application/json');
      request.send(body);
      await request.onLoad.first.timeout(const Duration(seconds: 90));
      if (request.status == 200) {
        final data = jsonDecode(request.responseText!);
        final text = data['response']?.toString().trim();
        if (text != null && text.isNotEmpty) return text;
        return 'Star has no recommendations right now.';
      } else {
        return 'Star encountered an error: ${request.status}';
      }
    } catch (e) {
      return 'Star is offline — run "ollama serve" to wake me up! Error: $e';
    }
  }

  static String buildPrompt({
    required String firstName,
    required int apsScore,
    required List<String> subjects,
    required List<String> careerInterests,
    String? province,
    bool needsFunding = false,
  }) {
    return '''
You are Star, a friendly South African university advisor assisting a student. Recommend 3 suitable universities and courses based on their profile. Keep it warm, encouraging, and practical.

Student Profile:
- Name: $firstName
- APS Score: $apsScore
- Subjects: ${subjects.join(', ')}
- Career Interests: ${careerInterests.join(', ')}
- Province: ${province ?? 'Not specified'}
- Needs Funding: ${needsFunding ? 'Yes' : 'Not specified'}

For each recommendation, include:
1. University name and why it matches
2. Suggested course/faculty
3. Any specific requirements they should know (NBT, APS minimum, fees)

Keep each recommendation to 2-3 sentences. Be encouraging and practical.
''';
  }
}
