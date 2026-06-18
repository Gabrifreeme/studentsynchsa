import 'dart:convert';
import 'package:http/http.dart' as http;

class AiService {
  static const _ollamaUrl = 'http://192.168.1.153:11434/api/generate';

  /// Ask Star for university recommendations based on profile data.
  static Future<String> ask(String prompt) async {
    try {
      final response = await http
          .post(
            Uri.parse(_ollamaUrl),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'model': 'qwen',
              'prompt': prompt,
              'stream': false,
            }),
          )
          .timeout(const Duration(seconds: 45));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final text = data['response']?.toString().trim();
        if (text != null && text.isNotEmpty) return text;
        return 'Star has no recommendations right now.';
      } else {
        return 'Star encountered an error: ${response.statusCode}';
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
