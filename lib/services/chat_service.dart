import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:hive/hive.dart';
import 'package:studentsyncsa/core/constants/app_constants.dart';
import 'package:uuid/uuid.dart';

/// Multi-user chat backed by Supabase's REST API (PostgREST).
/// No extra packages needed beyond http/hive/uuid, which the app already has.
/// If URL or key are empty, the caller falls back to device-local chat.
class ChatService {
  static const _urlKey = 'supabaseUrl';
  static const _keyKey = 'supabaseAnonKey';
  static const _uidKey = 'chatUserId';
  static const _table = 'app_messages';
  static const defaultRoom = 'general';

  static Box<String> get _settings => Hive.box<String>(AppConstants.settingsBox);

  static String get url {
    var u = (_settings.get(_urlKey) ?? '').trim();
    // Accept a full Data API URL or a dashboard URL and reduce it to the
    // base https://<ref>.supabase.co form the REST calls expect.
    if (u.endsWith('/')) u = u.substring(0, u.length - 1);
    u = u.replaceFirst(RegExp(r'/rest/v1/?$'), '');
    final dashboard = RegExp(r'^https://supabase\.com/dashboard/project/([^/]+)');
    final match = dashboard.firstMatch(u);
    if (match != null) u = 'https://${match.group(1)}.supabase.co';
    return u;
  }
  static String get key => (_settings.get(_keyKey) ?? '').trim();
  static bool get isConfigured => url.isNotEmpty && key.isNotEmpty;

  static Future<void> configure(String url, String key) async {
    await _settings.put(_urlKey, url.trim());
    await _settings.put(_keyKey, key.trim());
  }

  static int readCount(String room) =>
      int.tryParse(_settings.get('chat_read_$room') ?? '0') ?? 0;

  static Future<void> markRead(String room, int count) =>
      _settings.put('chat_read_$room', '$count');

  static String get myId {
    var id = _settings.get(_uidKey) ?? '';
    if (id.isEmpty) {
      id = const Uuid().v4();
      _settings.put(_uidKey, id);
    }
    return id;
  }

  static Map<String, String> get _headers => {
        'apikey': key,
        'Authorization': 'Bearer $key',
        'Content-Type': 'application/json',
      };

  static Future<List<Map<String, dynamic>>> fetchMessages(
      [String room = defaultRoom]) async {
    if (!isConfigured) return [];
    final uri = Uri.parse('$url/rest/v1/$_table')
        .replace(queryParameters: {
      'select': 'id,created_at,text,user_name,user_id,room',
      'room': 'eq.$room',
      'order': 'created_at.asc',
      'limit': '100',
    });
    final res = await http.get(uri, headers: _headers).timeout(
          const Duration(seconds: 12),
        );
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw Exception('Chat fetch failed (${res.statusCode}): ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static Future<void> sendMessage(String text, String userName,
      [String room = defaultRoom]) async {
    if (!isConfigured) return;
    final res = await http
        .post(
          Uri.parse('$url/rest/v1/$_table'),
          headers: {..._headers, 'Prefer': 'return=minimal'},
          body: jsonEncode({
            'text': text,
            'user_name': userName,
            'user_id': myId,
            'room': room,
          }),
        )
        .timeout(const Duration(seconds: 12));
    if (res.statusCode < 200 || res.statusCode >= 300) {
      throw Exception('Chat send failed (${res.statusCode}): ${res.body}');
    }
  }
}
