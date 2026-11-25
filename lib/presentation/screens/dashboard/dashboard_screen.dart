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
          title: const Text('LibSyncStudent',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, letterSpacing: -0.3)),
          actions: [
            IconButton(
              icon: const Icon(Icons.notifications_outlined),
              onPressed: () => context.push('/notifications'),
            ),
          ],
        ),
        body: Center(
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.7,
            ),
            child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Column(
            children: [
              _buildStarCta(context, firstName),
              const SizedBox(height: 10),
              _PrivacyConsentBanner(),
              const SizedBox(height: 10),
              _buildTileGrid(context),
            ],
          ),
        ),
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
              padding: const EdgeInsets.all(6),
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
              child: const StarAvatar(size: 64, pulse: true),
            ),
            const SizedBox(height: 8),
            Text(
              'Welcome, $firstName!',
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 20,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Tap the Star to begin',
              style: TextStyle(
                color: AppColors.textMuted,
                fontSize: 10,
                letterSpacing: 2,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTileGrid(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: AppSpaces.sm,
      crossAxisSpacing: AppSpaces.sm,
      childAspectRatio: 1.75,
      children: [
        AppListTile(
            icon: Icons.auto_awesome_rounded,
            label: 'ACEsi',
            value: '',
            compact: true,
            onTap: () => context.push('/ai-recommendations')),
        AppListTile(
            icon: Icons.person_rounded,
            label: 'My Profile',
            value: '',
            compact: true,
            onTap: () => context.push('/onboarding')),
        AppListTile(
            icon: Icons.chat_rounded,
            label: 'Community',
            value: '',
            compact: true,
            onTap: () => context.push('/chat')),
        AppListTile(
            icon: Icons.school_rounded,
            label: 'Universities',
            value: '',
            compact: true,
            onTap: () => context.push('/universities')),
        AppListTile(
            icon: Icons.assignment_rounded,
            label: 'Applications',
            value: '',
            compact: true,
            onTap: () => context.push('/applications')),
        AppListTile(
            icon: Icons.account_balance_rounded,
            label: 'Funding',
            value: '',
            compact: true,
            onTap: () => context.push('/funding')),
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
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: Row(
        children: [
          Icon(Icons.info_outline, color: AppColors.starGold, size: 16),
          const SizedBox(width: 6),
          Expanded(
            child: GestureDetector(
              onTap: () => context.push('/privacy'),
              child: const Text(
                'Review your Privacy Status here.',
                style: TextStyle(
                    color: AppColors.textSecondary, fontSize: 11),
              ),
            ),
          ),
          InkWell(
            onTap: _giveConsent,
            child: const Icon(
              Icons.check_box_outline_blank_rounded,
              color: AppColors.primary,
              size: 20,
            ),
          ),
        ],
      ),
    );
  }
}
