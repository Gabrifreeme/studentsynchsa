import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:uuid/uuid.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/domain/models/notification_item.dart';
import 'dart:convert';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

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
      'studentsyncsa Notifications',
      channelDescription: 'Notifications from studentsyncsa',
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
}
