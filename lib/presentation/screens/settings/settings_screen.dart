import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/sync_service.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text('Settings')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const SectionHeader(title: 'ACCOUNT'),
            const SizedBox(height: 8),
            AppCard(
              child: Column(
                children: [
                  _SettingTile(
                    icon: Icons.refresh_rounded,
                    label: 'Reset Profile',
                    color: AppColors.error,
                    onTap: () async {
                      await ref.read(authProvider.notifier).signOut();
                      if (context.mounted) context.go('/onboarding');
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const SectionHeader(title: 'STORAGE'),
            const SizedBox(height: 8),
            AppCard(
              child: Column(
                children: [
                  _SettingTile(
                    icon: Icons.delete_forever_rounded,
                    label: 'Clear All Local Data',
                    color: AppColors.error,
                    onTap: () => _confirmClear(context),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const SectionHeader(title: 'SYNC'),
            const SizedBox(height: 8),
            AppCard(
              child: Column(
                children: [
                  _SettingTile(
                    icon: Icons.sync_rounded,
                    label: 'Sync Now',
                    color: AppColors.info,
                    onTap: () {
                      SyncService.triggerSync();
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Syncing...')),
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            const SectionHeader(title: 'ABOUT'),
            const SizedBox(height: 8),
            AppCard(
              child: Column(
                children: [
                  _AboutRow('Version', '1.0.0'),
                  _AboutRow('Made for', 'South African Students'),
                  _AboutRow('AI Assistant', 'Star ⭐'),
                ],
              ),
            ),
            const SizedBox(height: 8),
            AppCard(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.shield_outlined, color: AppColors.success, size: 18),
                        const SizedBox(width: 8),
                        const Text('Privacy Status',
                            style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textPrimary)),
                      ],
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'All data is processed on-device. Nothing is sent to external servers.',
                      style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 8),
                    InkWell(
                      onTap: () => context.push('/privacy'),
                      borderRadius: BorderRadius.circular(8),
                      child: Row(
                        children: [
                          const Text('Full Privacy Notice',
                              style: TextStyle(
                                  fontSize: 13,
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w500)),
                          const SizedBox(width: 4),
                          Icon(Icons.open_in_new, size: 14, color: AppColors.primary),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _confirmClear(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Clear All Data?',
            style: TextStyle(color: AppColors.textPrimary)),
        content: const Text(
          'This will delete all your profile, applications, and saved data. This cannot be undone.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              await HiveDatabase.clearAll();
              if (ctx.mounted) Navigator.pop(ctx);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('All data cleared')),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.error),
            child: const Text('Clear'),
          ),
        ],
      ),
    );
  }
}

class _SettingTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _SettingTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: color),
      title: Text(label, style: const TextStyle(color: AppColors.textPrimary)),
      trailing: const Icon(Icons.chevron_right_rounded,
          color: AppColors.textMuted),
      onTap: onTap,
    );
  }
}

class _AboutRow extends StatelessWidget {
  final String label;
  final String value;
  const _AboutRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textSecondary)),
          Text(value, style: const TextStyle(color: AppColors.textPrimary)),
        ],
      ),
    );
  }
}
