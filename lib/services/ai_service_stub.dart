class AiService {
  static Future<void> warmUp() async {}
  static Future<void> askStream({
    required String prompt,
    required void Function(String token) onToken,
  }) async {
    onToken('Star AI is not available in this environment.');
  }
  static Future<String> ask(String prompt) async => 'Star AI is not available in this environment.';
  static String buildPrompt({
    required String firstName,
    required int apsScore,
    required List<String> subjects,
    required List<String> careerInterests,
    String? province,
    bool needsFunding = false,
  }) => '';
}
