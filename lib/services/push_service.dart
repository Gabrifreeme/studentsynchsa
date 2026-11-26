import 'dart:convert';
import 'dart:js_interop';

import 'package:http/http.dart' as http;
import 'package:studentsyncsa/services/chat_service.dart';

@JS('acePushRegister')
external JSPromise<JSString> acePushRegister(JSString vapidKey);

/// Browser Web Push registration for email alerts.
class PushService {
  // Public VAPID key — safe to ship in the app.
  static const vapidPublic =
      'BAXMWn6W-YogbHEXtwBmuWY02-mgrpwV2zjWxfRDamXpBwV2m-JtfGJpxS7viEG0OTX59z5kYtGyasPYaf5lzW0';

  static Future<Map<String, dynamic>> enable() async {
    try {
      final raw = await acePushRegister(vapidPublic.toJS).toDart;
      final result = jsonDecode(raw.toDart) as Map<String, dynamic>;
      if (result['ok'] != true) return result;
      await _save(
        '${result['endpoint']}',
        '${result['p256dh']}',
        '${result['auth']}',
      );
      return result;
    } catch (e) {
      return {'ok': false, 'error': '$e'};
    }
  }

  static Future<void> _save(
      String endpoint, String p256dh, String auth) async {
    if (!ChatService.isConfigured) return;
    final uri = Uri.parse('${ChatService.url}/rest/v1/push_subscriptions');
    final res = await http.post(
      uri,
      headers: {
        'apikey': ChatService.key,
        'Authorization': 'Bearer ${ChatService.key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
      },
      body: jsonEncode({
        'endpoint': endpoint,
        'p256dh': p256dh,
        'auth': auth,
      }),
    ).timeout(const Duration(seconds: 12));
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw Exception('Save subscription failed (${res.statusCode})');
    }
  }
}
