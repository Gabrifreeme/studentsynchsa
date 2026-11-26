import 'dart:convert';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/domain/models/notification_item.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// A notification pushed by ACEsi when a watched university/bursary email
/// arrives. This is an in-app message, not a connection to the mailbox.
class AppNotification {
  final int id;
  final String title;
  final String body;
  final String? sender;
  final DateTime createdAt;

  const AppNotification({
    required this.id,
    required this.title,
    required this.body,
    this.sender,
    required this.createdAt,
  });
}

class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _initialized = false;
  static const _remoteTable = 'app_notifications';
  static const _remoteReadKey = 'notif_remote_read_ids';

  static Future<void> init() async {
    if (_initialized) return;
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const settings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );
    await _plugin.initialize(settings);
    _initialized = true;
  }

  static Future<void> showNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'studentsyncsa_channel',
      'LibSyncStudent Notifications',
      channelDescription: 'Notifications from LibSyncStudent',
      importance: Importance.high,
      priority: Priority.high,
    );
    const iosDetails = DarwinNotificationDetails();
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    await _plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      details,
      payload: payload,
    );
  }

  static Future<void> addNotification({
    required String title,
    required String body,
    NotificationType type = NotificationType.general,
  }) async {
    final notification = NotificationItem(
      id: const Uuid().v4(),
      title: title,
      body: body,
      type: type,
    );
    final existing = await getNotifications();
    existing.insert(0, notification);
    final json = jsonEncode(existing.map((n) => n.toJson()).toList());
    await HiveDatabase.notifications.put('all', json);
    await showNotification(title: title, body: body);
  }

  static Future<List<NotificationItem>> getNotifications() async {
    final raw = HiveDatabase.notifications.get('all');
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List;
      return list.map((e) => NotificationItem.fromJson(e)).toList();
    } catch (_) {
      return [];
    }
  }

  static Future<int> getUnreadCount() async {
    final notifications = await getNotifications();
    return notifications.where((n) => !n.read).length;
  }

  static Future<void> markAsRead(String id) async {
    final notifications = await getNotifications();
    final index = notifications.indexWhere((n) => n.id == id);
    if (index != -1) {
      notifications[index] = notifications[index].copyWith(read: true);
      final json = jsonEncode(notifications.map((n) => n.toJson()).toList());
      await HiveDatabase.notifications.put('all', json);
    }
  }

  static Future<void> markAllAsRead() async {
    final notifications = await getNotifications();
    final updated = notifications.map((n) => n.copyWith(read: true)).toList();
    final json = jsonEncode(updated.map((n) => n.toJson()).toList());
    await HiveDatabase.notifications.put('all', json);
  }

  // ---- Email alerts pushed by ACEsi -------------------------------------

  static Map<String, String> get _remoteHeaders => {
        'apikey': ChatService.key,
        'Authorization': 'Bearer ${ChatService.key}',
        'Content-Type': 'application/json',
      };

  static Future<List<AppNotification>> fetchRemote() async {
    if (!ChatService.isConfigured) return [];
    final uri = Uri.parse('${ChatService.url}/rest/v1/$_remoteTable')
        .replace(queryParameters: {
      'select': 'id,created_at,title,body,sender',
      'order': 'created_at.desc',
      'limit': '20',
    });
    final res = await http.get(uri, headers: _remoteHeaders).timeout(
          const Duration(seconds: 12),
        );
    if (res.statusCode < 200 || res.statusCode >= 300) return [];
    final list = jsonDecode(res.body) as List<dynamic>;
    return list.map((e) {
      final m = Map<String, dynamic>.from(e as Map);
      return AppNotification(
        id: (m['id'] as num?)?.toInt() ?? 0,
        title: '${m['title'] ?? ''}',
        body: '${m['body'] ?? ''}',
        sender: m['sender'] as String?,
        createdAt: DateTime.tryParse('${m['created_at'] ?? ''}') ??
            DateTime.fromMillisecondsSinceEpoch(0),
      );
    }).toList();
  }

  static Set<String> _remoteReadIds() {
    final raw = HiveDatabase.settings.get(_remoteReadKey) ?? '';
    return raw.isEmpty ? <String>{} : raw.split(',').toSet();
  }

  static bool isRemoteRead(String id) => _remoteReadIds().contains(id);

  static Future<void> markRemoteRead(String id) async {
    final ids = _remoteReadIds();
    ids.add(id);
    await HiveDatabase.settings.put(_remoteReadKey, ids.join(','));
  }

  static Future<int> remoteUnreadCount() async {
    final rows = await fetchRemote();
    return rows.where((n) => !isRemoteRead('${n.id}')).length;
  }
}
