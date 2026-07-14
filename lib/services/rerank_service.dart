import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class RerankService {
  final String apiKey = dotenv.env['OPENROUTER_API_KEY'] ?? '';
  final String baseUrl = 'https://openrouter.ai/api/v1/rerank';
  
  Future<String?> getBestMatch(String fieldLabel, List<String> options) async {
    if (options.isEmpty || apiKey.isEmpty) return null;
    
    try {
      final response = await http.post(
        Uri.parse(baseUrl),
        headers: {
          'Authorization': 'Bearer ',
          'Content-Type': 'application/json',
          'HTTP-Referer': 'https://studentsyncsa.co.za',
        },
        body: jsonEncode({
          'model': 'nvidia/llama-nemotron-rerank-vl-1b-v2:free',
          'query': fieldLabel,
          'documents': options.map((text) => {'text': text}).toList(),
          'top_n': 1,
        }),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['results'].isNotEmpty) {
          final best = data['results'][0];
          final index = best['index'];
          return options[index];
        }
      }
      return null;
    } catch (e) {
      debugPrint('Rerank error: ');
      return null;
    }
  }
}
