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
          title: Column(
            mainAxisSize: MainAxisSize.min,
            children: const [
              Text('LibSyncStudent',
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.3)),
              Text('Powered by ACEsi',
                  style: TextStyle(
                      color: AppColors.starGold,
                      fontSize: 9,
                      fontWeight: FontWeight.w500)),
            ],
          ),
        ),
        body: Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: double.infinity,
            ),
            child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 40),
          child: Column(
            children: [
              _buildStarCta(context, firstName),
              const SizedBox(height: 7),
              _PrivacyConsentBanner(),
              const SizedBox(height: 7),
              _buildTileGrid(context, isRight, ref),
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
              padding: const EdgeInsets.all(4),
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
            const SizedBox(height: 6),
            Text(
              'Welcome, $firstName!',
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 4),
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

  Widget _buildTileGrid(BuildContext context, bool isRight, WidgetRef ref) {
    void openMenu() {
      final scaffold = Scaffold.of(context);
      if (isRight) {
        scaffold.openEndDrawer();
      } else {
        scaffold.openDrawer();
      }
    }

    Widget tile(IconData icon, String label, String route) {
      return AppListTile(
        icon: icon,
        label: label,
        value: '',
        compact: true,
        onTap: () => context.push(route),
      );
    }

    return Column(
      children: [
        Row(
          children: [
            IconButton(
              icon: StarIcon(
                  isRight ? Icons.menu_open_rounded : Icons.menu_rounded,
                  size: 20),
              onPressed: openMenu,
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),
            const SizedBox(width: AppSpaces.xs),
            Expanded(child: tile(Icons.auto_awesome_rounded, 'ACEsi', '/ai-recommendations')),
            const SizedBox(width: AppSpaces.sm),
            Expanded(child: tile(Icons.person_rounded, 'My Profile', '/onboarding')),
            const SizedBox(width: AppSpaces.xs),
            IconButton(
              icon: const StarIcon(Icons.notifications_outlined, size: 20),
              onPressed: () => context.push('/notifications'),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            ),
          ],
        ),
        const SizedBox(height: AppSpaces.sm),
        Row(
          children: [
            Expanded(child: tile(Icons.chat_rounded, 'Community', '/chat')),
            const SizedBox(width: AppSpaces.sm),
            Expanded(child: tile(Icons.school_rounded, 'Universities', '/universities')),
          ],
        ),
        const SizedBox(height: AppSpaces.sm),
        Row(
          children: [
            Expanded(child: tile(Icons.assignment_rounded, 'Applications', '/applications')),
            const SizedBox(width: AppSpaces.sm),
            Expanded(child: tile(Icons.account_balance_rounded, 'Funding', '/funding')),
          ],
        ),
        const SizedBox(height: AppSpaces.sm),
        Row(
          children: [
            Expanded(child: tile(Icons.settings_rounded, 'Settings', '/settings')),
            const SizedBox(width: AppSpaces.sm),
            Expanded(child: tile(Icons.info_outline_rounded, 'About Us', '/about')),
          ],
        ),
        const SizedBox(height: 166),
        Center(
          child: OutlinedButton.icon(
            onPressed: () async {
              await ref.read(authProvider.notifier).signOut();
              if (context.mounted) context.go('/login');
            },
            icon: const StarIcon(Icons.logout_rounded, size: 16),
            label: const Text('Exit'),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(120, 34),
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 4),
              textStyle: const TextStyle(fontSize: 9),
              side: const BorderSide(color: AppColors.primary),
            ),
          ),
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
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 6),
      child: Row(
        children: [
          Icon(Icons.info_outline, color: AppColors.starGold, size: 16),
          const SizedBox(width: 4),
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
