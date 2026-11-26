import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/providers/sidebar_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
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
    final isRight = ref.watch(sidebarProvider) == SidebarPosition.right;

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          leading: IconButton(
            icon: StarIcon(
                isRight ? Icons.menu_open_rounded : Icons.menu_rounded,
                size: 20),
            tooltip: 'Open menu',
            onPressed: () {
              // The drawer lives on the shell Scaffold, not on this screen's
              // own Scaffold, so walk up to the one that actually has it.
              ScaffoldState? shell;
              context.visitAncestorElements((element) {
                if (element is StatefulElement &&
                    element.state is ScaffoldState) {
                  final s = element.state as ScaffoldState;
                  if (s.widget.drawer != null || s.widget.endDrawer != null) {
                    shell = s;
                    return false;
                  }
                }
                return true;
              });
              if (shell == null) return;
              if (isRight) {
                shell!.openEndDrawer();
              } else {
                shell!.openDrawer();
              }
            },
          ),
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
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Column(
            children: [
              _buildStarCta(context, firstName),
              const SizedBox(height: 7),
              _PrivacyConsentBanner(),
              const SizedBox(height: 16),
              _buildTileGrid(context, isRight, ref),
            ],
          ),
        ),
          ),
        ),
      ),
    );
  }

  /// Bottom-centre card for email alerts pushed by ACEsi.
  Widget _buildEmailCard(BuildContext context) =>
      FutureBuilder<List<AppNotification>>(
        future: NotificationService.fetchRemote(),
        builder: (context, snap) {
          final rows = snap.data ?? const <AppNotification>[];
          final count = rows
              .where((n) => !NotificationService.isRemoteRead('${n.id}'))
              .length;
          final latest = rows.isNotEmpty ? rows.first : null;
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 340),
              child: SizedBox(
                width: double.infinity,
                child: AppCard(
                  onTap: () => context.push('/email-notifications'),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  child: Row(
                    children: [
                      const StarIcon(Icons.mail_outline_rounded, size: 18),
                      const SizedBox(width: 7),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Email',
                              style: TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700),
                            ),
                            if (latest != null)
                              Text(
                                latest.title,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                    color: AppColors.textMuted, fontSize: 9),
                              ),
                          ],
                        ),
                      ),
                      if (count > 0)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 5, vertical: 1),
                          decoration: const BoxDecoration(
                              color: Color(0xFFFF4444), shape: BoxShape.circle),
                          child: Text('$count',
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 9,
                                  fontWeight: FontWeight.w700)),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      );

  Widget _buildStarCta(BuildContext context, String firstName) {
    final mobile = MediaQuery.of(context).size.width < 600;
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
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: mobile ? 18 : 14,
                fontWeight: FontWeight.w900,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Tap the Star to begin',
              style: TextStyle(
                color: AppColors.textMuted,
                fontSize: mobile ? 12 : 10,
                letterSpacing: mobile ? 1.4 : 2,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTileGrid(BuildContext context, bool isRight, WidgetRef ref) {
    Widget tile(IconData icon, String label, String route,
        {String badge = ''}) {
      return AppListTile(
        icon: icon,
        label: label,
        value: badge,
        compact: true,
        onTap: () => context.push(route),
      );
    }

    return Column(
      children: [
        Row(
          children: [
            Expanded(
                child: tile(Icons.auto_awesome_rounded, 'ACEsi',
                    '/ai-recommendations')),
            const SizedBox(width: AppSpaces.sm),
            Expanded(child: tile(Icons.person_rounded, 'My Profile', '/onboarding')),
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
            Expanded(
              child: FutureBuilder<int>(
                future: NotificationService.remoteUnreadCount(),
                builder: (context, snap) {
                  final count = snap.data ?? 0;
                  return tile(
                    Icons.assignment_rounded,
                    'Your Progress',
                    '/applications',
                    badge: count > 0 ? '$count' : '',
                  );
                },
              ),
            ),
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
        const SizedBox(height: 8),
        _buildEmailCard(context),
        const SizedBox(height: 8),
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
              child: Text.rich(
                TextSpan(
                  children: [
                    TextSpan(
                      text: 'Review your Privacy Status ',
                      style: const TextStyle(
                          color: AppColors.textSecondary, fontSize: 13),
                    ),
                    TextSpan(
                      text: 'HERE',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        background: Paint()
                          ..color = AppColors.primary.withValues(alpha: 0.22),
                      ),
                    ),
                    const TextSpan(
                      text: '.',
                      style: TextStyle(
                          color: AppColors.textSecondary, fontSize: 13),
                    ),
                  ],
                ),
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
