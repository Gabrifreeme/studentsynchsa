import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

class AiService {
  // ACEsi's own Groq -> Gemini stream endpoint, proxied by the app's web
  // server so the phone never talks to a third-party API directly.
  static Uri get _endpoint => Uri.base.resolve('api/ai/ask');

  static Future<void> warmUp() async {}

  static Future<void> askStream({
    required String prompt,
    required void Function(String token) onToken,
  }) async {
    try {
      final response = await http
          .post(
            _endpoint,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'prompt': prompt}),
          )
          .timeout(const Duration(seconds: 150));

      if (response.statusCode != 200) {
        onToken('ACEsi error: HTTP ${response.statusCode}');
        return;
      }
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final error = data['error'] as String?;
      if (error != null && error.isNotEmpty) {
        onToken('ACEsi error: $error');
        return;
      }
      final reply = data['reply'] as String? ?? '';
      if (reply.isNotEmpty) onToken(reply);
    } on TimeoutException {
      onToken('ACEsi is taking too long. Please try again.');
    } catch (e) {
      onToken('Could not reach ACEsi. Check your connection and try again.');
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
