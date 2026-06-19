import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/notification_service.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<dynamic> _notifications = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final notifications = await NotificationService.getNotifications();
    setState(() {
      _notifications = notifications;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('Notifications'),
          actions: [
            if (_notifications.isNotEmpty)
              TextButton(
                onPressed: () async {
                  await NotificationService.markAllAsRead();
                  _load();
                },
                child: const Text('Mark all read'),
              ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : _notifications.isEmpty
                ? const EmptyState(
                    icon: Icons.notifications_none_rounded,
                    title: 'No notifications yet',
                    subtitle: 'You\'ll see updates about deadlines, applications, and sync status here')
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _notifications.length,
                    itemBuilder: (_, i) {
                      final n = _notifications[i] as dynamic;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: AppCard(
                          child: InkWell(
                            onTap: () async {
                              await NotificationService.markAsRead(n.id);
                              _load();
                            },
                            borderRadius: BorderRadius.circular(16),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 40,
                                  height: 40,
                                  decoration: BoxDecoration(
                                    color: n.read
                                        ? AppColors.surfaceLight
                                        : AppColors.primary.withValues(alpha: 0.2),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Icon(
                                    _iconForType(n.type),
                                    color: n.read
                                        ? AppColors.textMuted
                                        : AppColors.primaryLight,
                                    size: 20,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        n.title ?? '',
                                        style: TextStyle(
                                          color: n.read
                                              ? AppColors.textSecondary
                                              : AppColors.textPrimary,
                                          fontWeight: n.read
                                              ? FontWeight.normal
                                              : FontWeight.bold,
                                          fontSize: 14,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        n.body ?? '',
                                        style: const TextStyle(
                                          color: AppColors.textMuted,
                                          fontSize: 12,
                                        ),
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        DateFormat('MMM d, HH:mm')
                                            .format(n.createdAt as DateTime),
                                        style: const TextStyle(
                                          color: AppColors.textMuted,
                                          fontSize: 10,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                if (!(n.read ?? false))
                                  Container(
                                    width: 8,
                                    height: 8,
                                    decoration: const BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: AppColors.primary,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
      ),
    );
  }

  IconData _iconForType(dynamic type) {
    switch (type) {
      case 'deadline':
        return Icons.access_time_rounded;
      case 'statusChange':
        return Icons.swap_horiz_rounded;
      case 'syncComplete':
        return Icons.cloud_done_rounded;
      case 'profileReminder':
        return Icons.person_outline_rounded;
      default:
        return Icons.notifications_outlined;
    }
  }
}
