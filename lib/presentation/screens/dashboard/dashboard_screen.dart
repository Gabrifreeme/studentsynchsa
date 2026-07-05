import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/providers/sidebar_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

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
    final isRight = ref.watch(sidebarProvider) == SidebarPosition.right;

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          leading: IconButton(
            icon: Icon(isRight ? Icons.menu_open_rounded : Icons.menu_rounded),
            onPressed: () {
              final scaffold = Scaffold.of(context);
              if (isRight) {
                scaffold.openEndDrawer();
              } else {
                scaffold.openDrawer();
              }
            },
          ),
          title: const Text('StudentSyncSA',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: -0.3)),
          actions: [
            IconButton(
              icon: const Icon(Icons.notifications_outlined),
              onPressed: () => context.push('/notifications'),
            ),
          ],
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              const SizedBox(height: 32),
              _buildStarCta(context, firstName),
              const SizedBox(height: 48),
              _PrivacyConsentBanner(),
              const SizedBox(height: 24),
              _buildQuickLinks(context),
              const SizedBox(height: 8),
              _buildProgressCards(context),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStarCta(BuildContext context, String firstName) {
    return GestureDetector(
      onTap: () => context.push('/ai-recommendations'),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primary.withValues(alpha: 0.15),
                    blurRadius: 60,
                    spreadRadius: 10,
                  ),
                ],
              ),
              child: const StarAvatar(size: 120, pulse: true),
            ),
            const SizedBox(height: 20),
            Text(
              'Welcome, $firstName!',
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 28,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Tap the Star to begin',
              style: TextStyle(
                color: AppColors.textMuted,
                fontSize: 13,
                letterSpacing: 3,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
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

    return AppCard(
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
                    text: TextSpan(
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppColors.textSecondary,
                        height: 1.4,
                      ),
                      children: [
                        const TextSpan(
                          text: 'Star recommends reviewing your ',
                        ),
                        WidgetSpan(
                          child: GestureDetector(
                            onTap: () => context.push('/privacy'),
                            child: const Text(
                              'Privacy Status',
                              style: TextStyle(
                                fontSize: 14,
                                color: AppColors.primary,
                                fontWeight: FontWeight.w700,
                                decoration: TextDecoration.underline,
                              ),
                            ),
                          ),
                        ),
                        const TextSpan(text: ' here.'),
                      ],
                    ),
                    textScaler: TextScaler.linear(0.92),
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
                        fontSize: 13,
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
                fontSize: 12,
                color: AppColors.textMuted,
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
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.3)),
                  Text(value,
                      style: const TextStyle(
                          color: AppColors.textSecondary, fontSize: 14)),
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
