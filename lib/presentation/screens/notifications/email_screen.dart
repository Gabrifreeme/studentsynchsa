import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/notification_service.dart';

/// Email alerts pushed by ACEsi when a watched university/bursary email
/// arrives. This screen does not read the student's mailbox.
class EmailScreen extends StatefulWidget {
  const EmailScreen({super.key});

  @override
  State<EmailScreen> createState() => _EmailScreenState();
}

class _EmailScreenState extends State<EmailScreen> {
  Future<void> _refresh() async {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text('Email')),
        body: FutureBuilder<List<AppNotification>>(
          future: NotificationService.fetchRemote(),
          builder: (context, snap) {
            final rows = snap.data ?? const <AppNotification>[];
            if (rows.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    'No email notifications yet. Alerts from universities '
                    'and bursaries will appear here.',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 12),
                  ),
                ),
              );
            }
            return RefreshIndicator(
              onRefresh: _refresh,
              child: ListView.builder(
                padding: const EdgeInsets.all(10),
                itemCount: rows.length,
                itemBuilder: (_, i) {
                  final n = rows[i];
                  final unread = !NotificationService.isRemoteRead('${n.id}');
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: AppCard(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 8),
                      onTap: () async {
                        // One tap clears the unread highlight, then asks.
                        await NotificationService.markRemoteRead('${n.id}');
                        await _refresh();
                        await showDialog<bool>(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            backgroundColor: AppColors.surface,
                            title: const Text(
                              'Open Email?',
                              style: TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w700),
                            ),
                            content: Text(
                              '${n.title}\n\n${n.body}',
                              style: const TextStyle(
                                  color: AppColors.textSecondary, fontSize: 12),
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(ctx, false),
                                child: const Text('Cancel'),
                              ),
                              ElevatedButton(
                                onPressed: () => Navigator.pop(ctx, true),
                                child: const Text('Open'),
                              ),
                            ],
                          ),
                        );
                      },
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.mail_outline_rounded,
                              size: 20,
                              color: unread
                                  ? AppColors.primary
                                  : AppColors.textMuted),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(n.title,
                                    style: TextStyle(
                                        color: unread
                                            ? AppColors.primary
                                            : AppColors.textPrimary,
                                        fontSize: 12,
                                        fontWeight: unread
                                            ? FontWeight.w700
                                            : FontWeight.w500)),
                                const SizedBox(height: 4),
                                Text(n.body,
                                    style: const TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 11)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            );
          },
        ),
      ),
    );
  }
}
