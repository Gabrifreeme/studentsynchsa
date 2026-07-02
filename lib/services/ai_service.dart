import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class AiService {
  static const _apiKey = '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';
  static const _baseUrl = 'https://integrate.api.nvidia.com/v1';
  static const _model = 'meta/llama-3.1-70b-instruct';

  static Future<void> warmUp() async {}

  static Future<void> askStream({
    required String prompt,
    required void Function(String token) onToken,
  }) async {
    try {
      final client = http.Client();
      try {
        final uri = Uri.parse('$_baseUrl/chat/completions');
        final body = jsonEncode({
          'model': _model,
          'messages': [
            {
              'role': 'system',
              'content': 'You are Star, a friendly South African university application advisor. You help students with applications, university choices, bursaries, and career guidance. Keep responses helpful and concise.',
            },
            {'role': 'user', 'content': prompt},
          ],
          'max_tokens': 1024,
          'stream': true,
        });

        final request = http.Request('POST', uri)
          ..headers['Content-Type'] = 'application/json'
          ..headers['Authorization'] = 'Bearer $_apiKey'
          ..body = body;

        final response = await client
            .send(request)
            .timeout(const Duration(seconds: 30));

        final stream = response.stream
            .transform(utf8.decoder)
            .transform(const LineSplitter());

        await for (final line in stream) {
          if (line.trim().isEmpty) continue;
          if (line == 'data: [DONE]') break;
          if (!line.startsWith('data: ')) continue;
          try {
            final data = jsonDecode(line.substring(6)) as Map<String, dynamic>;
            final delta = data['choices']?[0]?['delta'] as Map<String, dynamic>?;
            final token = delta?['content'] as String?;
            if (token != null && token.isNotEmpty) {
              onToken(token);
            }
          } catch (_) {}
        }
      } finally {
        client.close();
      }
    } on TimeoutException {
      onToken('Star AI is taking too long. Please try again.');
    } catch (e) {
      onToken('Could not connect to Star AI. Check your internet connection.');
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
    return '''Hello! I am $firstName. My APS score is $apsScore. I take ${subjects.join(', ')}. I am interested in ${careerInterests.join(', ')}. I am from ${province ?? 'South Africa'}${needsFunding ? ' and I need funding.' : '.'}

What universities and courses do you recommend for me?''';
  }
}
