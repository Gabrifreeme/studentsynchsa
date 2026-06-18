import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/presentation/providers/auth_provider.dart';
import 'package:studentsynchsa/presentation/providers/profile_provider.dart';
import 'package:studentsynchsa/presentation/providers/sync_provider.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';
import 'package:studentsynchsa/services/sync_service.dart' as sync_service;
import 'package:studentsynchsa/services/notification_service.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authAsync = ref.watch(authProvider);
    final profileAsync = ref.watch(profileProvider);
    final profile = profileAsync.valueOrNull ?? authAsync.valueOrNull?.profile;
    final firstName = profile?.firstName.isNotEmpty == true
        ? profile!.firstName
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
              const Text('StudentSynchSA', style: TextStyle(fontSize: 16)),
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
                            profile?.email ?? '',
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
              const SizedBox(height: 20),

              // Quick Actions Grid
              const SectionHeader(title: 'QUICK ACTIONS'),
              const SizedBox(height: 12),
              _buildQuickActions(context, ref),
              const SizedBox(height: 24),

              // Star Recommendation Prompt
              _buildStarPrompt(context, firstName, profile?.apsScore),
              const SizedBox(height: 20),

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

  Widget _buildQuickActions(BuildContext context, WidgetRef ref) {
    final actions = [
      _ActionItem(
        icon: Icons.calculate_rounded,
        label: 'APS Calculator',
        color: const Color(0xFF7C3AED),
        onTap: () => context.push('/aps-calculator'),
      ),
      _ActionItem(
        icon: Icons.auto_awesome_rounded,
        label: 'Star AI',
        color: AppColors.starGold,
        onTap: () => context.push('/ai-recommendations'),
      ),
      _ActionItem(
        icon: Icons.person_rounded,
        label: 'My Profile',
        color: const Color(0xFF3B82F6),
        onTap: () => context.push('/onboarding'),
      ),
      _ActionItem(
        icon: Icons.chat_rounded,
        label: 'Community',
        color: const Color(0xFF22C55E),
        onTap: () => context.push('/chat'),
      ),
    ];

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 1.2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: actions.length,
      itemBuilder: (_, i) => _ActionCard(action: actions[i]),
    );
  }

  Widget _buildStarPrompt(BuildContext context, String name, int? aps) {
    return AppCard(
      child: Row(
        children: [
          const StarAvatar(size: 48),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Ask Star',
                  style: TextStyle(
                    color: AppColors.starGold,
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  aps != null
                      ? 'Your APS is $aps. Want university recommendations?'
                      : 'Complete your profile and Star will guide you!',
                  style: const TextStyle(
                      color: AppColors.textSecondary, fontSize: 12),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.arrow_forward_rounded,
                color: AppColors.starGold),
            onPressed: () => context.push('/ai-recommendations'),
          ),
        ],
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

class _ActionItem {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  const _ActionItem({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });
}

class _ActionCard extends StatelessWidget {
  final _ActionItem action;
  const _ActionCard({required this.action});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: action.onTap,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              action.color.withValues(alpha: 0.2),
              action.color.withValues(alpha: 0.05),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: action.color.withValues(alpha: 0.3)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(action.icon, color: action.color, size: 32),
            const SizedBox(height: 8),
            Text(
              action.label,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
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
