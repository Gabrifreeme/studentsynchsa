enum NotificationType {
  deadline,
  statusChange,
  syncComplete,
  profileReminder,
  general;

  String get label {
    switch (this) {
      case deadline: return 'Deadline';
      case statusChange: return 'Status Change';
      case syncComplete: return 'Sync Complete';
      case profileReminder: return 'Profile Reminder';
      case general: return 'General';
    }
  }
}

class NotificationItem {
  final String id;
  final String title;
  final String body;
  final NotificationType type;
  final DateTime createdAt;
  final bool read;

  NotificationItem({
    required this.id,
    required this.title,
    required this.body,
    this.type = NotificationType.general,
    DateTime? createdAt,
    this.read = false,
  }) : createdAt = createdAt ?? DateTime.now();

  NotificationItem copyWith({bool? read}) => NotificationItem(
    id: id,
    title: title,
    body: body,
    type: type,
    createdAt: createdAt,
    read: read ?? this.read,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'body': body,
    'type': type.name,
    'createdAt': createdAt.toIso8601String(),
    'read': read,
  };

  factory NotificationItem.fromJson(Map<String, dynamic> json) => NotificationItem(
    id: json['id'] ?? '',
    title: json['title'] ?? '',
    body: json['body'] ?? '',
    type: NotificationType.values.firstWhere((t) => t.name == json['type'], orElse: () => NotificationType.general),
    createdAt: DateTime.parse(json['createdAt']),
    read: json['read'] ?? false,
  );
}
