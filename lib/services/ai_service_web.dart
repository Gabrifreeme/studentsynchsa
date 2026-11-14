import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:universal_html/html.dart';

class AiService {
  static const String _endpoint = 'http://127.0.0.1:5000/api/ai/chat';

  static Future<void> warmUp() async {}

  static Future<void> askStream({
    required String prompt,
    required void Function(String token) onToken,
  }) async {
    try {
      final body = jsonEncode({'prompt': prompt});
      final request = HttpRequest();
      request.open('POST', _endpoint, async: true);
      request.setRequestHeader('Content-Type', 'application/json; charset=utf-8');
      request.responseType = 'arraybuffer';

      final completer = Completer<void>();

      request.onLoadEnd.listen((_) {
        if (completer.isCompleted) return;
        try {
          final raw = request.response;
          String text;
          if (raw is String) {
            text = raw;
          } else {
            final responseBytes = _extractBytes(raw);
            if (responseBytes == null || responseBytes.isEmpty) {
              onToken('Star AI error: empty response');
              completer.complete();
              return;
            }
            text = utf8.decode(responseBytes, allowMalformed: true);
          }
          _parseAndEmit(text, onToken);
          completer.complete();
        } catch (e) {
          onToken('Star AI error: $e');
          if (!completer.isCompleted) completer.complete();
        }
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

  static List<int>? _extractBytes(dynamic raw) {
    if (raw == null) return null;
    if (raw is ByteBuffer) return raw.asUint8List();
    if (raw is Uint8List) return raw;
    if (raw is List<int>) return raw;
    if (raw is String) {
      // Got a String back (responseType ignored). Handle as text directly,
      // not as bytes -- it's already a Dart string, repairs happen later.
      return null;
    }
    return null;
  }

  static const Map<int, int> _cp1252HighMap = {
    0x20AC: 0x80, 0x201A: 0x82, 0x0192: 0x83, 0x201E: 0x84,
    0x2026: 0x85, 0x2020: 0x86, 0x2021: 0x87, 0x02C6: 0x88,
    0x2030: 0x89, 0x0160: 0x8A, 0x2039: 0x8B, 0x0152: 0x8C,
    0x017D: 0x8E, 0x2018: 0x91, 0x2019: 0x92, 0x201C: 0x93,
    0x201D: 0x94, 0x2022: 0x95, 0x2013: 0x96, 0x2014: 0x97,
    0x02DC: 0x98, 0x2122: 0x99, 0x0161: 0x9A, 0x203A: 0x9B,
    0x0153: 0x9C, 0x017E: 0x9E, 0x0178: 0x9F,
  };

  static String _fixMangled(String s) {
    if (s.isEmpty) return s;
    bool hasHigh = false;
    for (final r in s.runes) {
      if (r > 127) { hasHigh = true; break; }
    }
    if (!hasHigh) return s;

    final bytes = <int>[];
    for (final r in s.runes) {
      if (r <= 0xFF) {
        bytes.add(r);
      } else if (_cp1252HighMap.containsKey(r)) {
        bytes.add(_cp1252HighMap[r]!);
      } else {
        bytes.addAll(utf8.encode(String.fromCharCode(r)));
      }
    }
    try {
      return utf8.decode(bytes, allowMalformed: true);
    } catch (_) {
      return s;
    }
  }

  static void _parseAndEmit(String text, void Function(String) onToken) {
    final pending = StringBuffer()..write(text);
    while (true) {
      final current = pending.toString();
      final sepIdx = current.indexOf('\n\n');
      if (sepIdx == -1) break;
      final event = current.substring(0, sepIdx);
      final remainder = current.substring(sepIdx + 2);
      pending
        ..clear()
        ..write(remainder);
      for (final line in event.split('\n')) {
        if (!line.startsWith('data:')) continue;
        final payload = line.substring(5).trim();
        if (payload.isEmpty || payload == '[DONE]') continue;
        try {
          final data = jsonDecode(payload);
          if (data is Map) {
            final tok = data['token'];
            if (tok is String && tok.isNotEmpty) onToken(_fixMangled(tok));
            final err = data['error'];
            if (err is String && err.isNotEmpty) onToken(' [error: $err]');
          }
        } catch (_) {}
      }
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
