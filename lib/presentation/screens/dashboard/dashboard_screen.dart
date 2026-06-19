import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/providers/sync_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/sync_service.dart' as sync_service;
import 'package:studentsyncsa/services/notification_service.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authAsync = ref.watch(authProvider);
    final profileAsync = ref.watch(profileProvider);
    final profile = profileAsync.valueOrNull ?? authAsync.valueOrNull?.profile;
    final firstName = profile?.personal.firstName.isNotEmpty == true
        ? profile!.personal.firstName
        : 'Student';

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const StarAvatar(size: 32),
              const SizedBox(width: 8),
              const Text('studentsyncsa', style: TextStyle(fontSize: 16)),
            ],
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.notifications_outlined),
              onPressed: () => context.push('/notifications'),
            ),
            IconButton(
              icon: const Icon(Icons.settings_outlined),
              onPressed: () => context.push('/settings'),
            ),
          ],
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Card
              AppCard(
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 28,
                      backgroundColor: AppColors.primary,
                      child: Text(
                        firstName[0].toUpperCase(),
                        style: const TextStyle(
                            fontSize: 24,
                            color: Colors.white,
                            fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Welcome, $firstName!',
                            style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            profile?.contact.email ?? '',
                            style: const TextStyle(
                                fontSize: 12, color: AppColors.textSecondary),
                          ),
                          const SizedBox(height: 4),
                          _buildSyncStatus(ref),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Star — center stage
              _buildStarCta(context),
              _PrivacyConsentBanner(),
              const SizedBox(height: 24),

              // Quick Links
              const SectionHeader(title: 'QUICK LINKS'),
              const SizedBox(height: 12),
              _buildQuickLinks(context),
              const SizedBox(height: 24),

              // Recent / Status
              const SectionHeader(title: 'YOUR PROGRESS'),
              const SizedBox(height: 12),
              _buildProgressCards(context),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSyncStatus(WidgetRef ref) {
    return ref.watch(syncStatusNotifierProvider).when(
          data: (status) {
            String label;
            switch (status) {
              case sync_service.SyncStatus.syncing:
                label = 'syncing';
                break;
              case sync_service.SyncStatus.synced:
                label = 'synced';
                break;
              case sync_service.SyncStatus.failed:
                label = 'failed';
                break;
              case sync_service.SyncStatus.offline:
                label = 'offline';
                break;
            }
            return SyncStatusBadge(status: label);
          },
          loading: () => const SizedBox.shrink(),
          error: (_, __) => const SizedBox.shrink(),
        );
  }

  Widget _buildQuickLinks(BuildContext context) {
    return Column(
      children: [
        _ProgressTile(
          icon: Icons.person_rounded,
          label: 'My Profile',
          value: 'View and edit your profile',
          onTap: () => context.push('/onboarding'),
        ),
        const SizedBox(height: 8),
        _ProgressTile(
          icon: Icons.chat_rounded,
          label: 'Community',
          value: 'Chat with other students',
          onTap: () => context.push('/chat'),
        ),
      ],
    );
  }

  Widget _buildStarCta(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/ai-recommendations'),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.4),
                    blurRadius: 16,
                    spreadRadius: 3,
                  ),
                ],
              ),
              child: const StarAvatar(size: 80, pulse: true),
            ),
            const SizedBox(height: 12),
            const Text(
              'Click me!',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressCards(BuildContext context) {
    return Column(
      children: [
        _ProgressTile(
          icon: Icons.school_rounded,
          label: 'Universities',
          value: '26 available',
          onTap: () => context.push('/universities'),
        ),
        const SizedBox(height: 8),
        _ProgressTile(
          icon: Icons.assignment_rounded,
          label: 'Applications',
          value: 'Track your progress',
          onTap: () => context.push('/applications'),
        ),
        const SizedBox(height: 8),
        _ProgressTile(
          icon: Icons.account_balance_rounded,
          label: 'Funding',
          value: 'Bursaries & scholarships',
          onTap: () => context.push('/funding'),
        ),
      ],
    );
  }
}

class _PrivacyConsentBanner extends StatefulWidget {
  @override
  State<_PrivacyConsentBanner> createState() => _PrivacyConsentBannerState();
}

class _PrivacyConsentBannerState extends State<_PrivacyConsentBanner> {
  bool _consented = false;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    try {
      final val = HiveDatabase.settings.get('privacyConsentGiven');
      if (val == 'true') {
        _consented = true;
      }
    } catch (_) {}
    _initialized = true;
  }

  void _giveConsent() {
    HiveDatabase.settings.put('privacyConsentGiven', 'true');
    setState(() => _consented = true);
  }

  @override
  Widget build(BuildContext context) {
    if (!_initialized || _consented) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: AppCard(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline, color: AppColors.starGold, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: RichText(
                      textScaleFactor: 0.92,
                      text: TextSpan(
                        style: const TextStyle(
                          fontSize: 13,
                          color: AppColors.textSecondary,
                          height: 1.4,
                        ),
                        children: [
                          const TextSpan(
                            text: 'Star highly recommends you head over to our ',
                          ),
                          WidgetSpan(
                            child: GestureDetector(
                              onTap: () => context.push('/privacy'),
                              child: const Text(
                                'Privacy Status',
                                style: TextStyle(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w600,
                                  decoration: TextDecoration.underline,
                                ),
                              ),
                            ),
                          ),
                          const TextSpan(text: ' by tapping here.'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              InkWell(
                onTap: _giveConsent,
                borderRadius: BorderRadius.circular(8),
                child: Row(
                  children: [
                    Icon(
                      _consented
                          ? Icons.check_box_rounded
                          : Icons.check_box_outline_blank_rounded,
                      color: AppColors.primary,
                      size: 22,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'I have read and consent to the privacy policy',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'You can review consent anytime via Settings > Privacy & Compliance.',
                style: TextStyle(
                  fontSize: 11,
                  color: AppColors.textMuted,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProgressTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final VoidCallback onTap;

  const _ProgressTile({
    required this.icon,
    required this.label,
    required this.value,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AppCard(
        child: Row(
          children: [
            Icon(icon, color: AppColors.primaryLight, size: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w600)),
                  Text(value,
                      style: const TextStyle(
                          color: AppColors.textSecondary, fontSize: 12)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded,
                color: AppColors.textMuted, size: 20),
          ],
        ),
      ),
    );
  }
}
