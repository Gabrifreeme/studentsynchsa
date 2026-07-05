import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/providers/sidebar_provider.dart';
import 'package:studentsyncsa/presentation/screens/auth/signup_screen.dart';
import 'package:studentsyncsa/presentation/screens/auth/fake_download_screen.dart';
import 'package:studentsyncsa/presentation/screens/dashboard/dashboard_screen.dart';
import 'package:studentsyncsa/presentation/screens/profile/profile_onboarding_screen.dart';
import 'package:studentsyncsa/presentation/screens/universities/universities_screen.dart';
import 'package:studentsyncsa/presentation/screens/universities/university_detail_screen.dart';
import 'package:studentsyncsa/presentation/screens/aps/aps_calculator_screen.dart';
import 'package:studentsyncsa/presentation/screens/applications/application_tracker_screen.dart';
import 'package:studentsyncsa/presentation/screens/funding/funding_list_screen.dart';
import 'package:studentsyncsa/presentation/screens/funding/funding_detail_screen.dart';
import 'package:studentsyncsa/presentation/screens/ai_recommendations/ai_recommendations_screen.dart';
import 'package:studentsyncsa/presentation/screens/notifications/notifications_screen.dart';
import 'package:studentsyncsa/presentation/screens/chat/chat_screen.dart';
import 'package:studentsyncsa/presentation/screens/settings/settings_screen.dart';
import 'package:studentsyncsa/presentation/screens/settings/privacy_screen.dart';
import 'package:studentsyncsa/presentation/screens/universities/application_helper_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

final GlobalKey<NavigatorState> _rootNavigator = GlobalKey<NavigatorState>();

final _authRefresh = ValueNotifier<int>(0);

void triggerAuthRedirect() {
  _authRefresh.value++;
}

final appRouter = GoRouter(
  navigatorKey: _rootNavigator,
  initialLocation: '/fake-download',
  refreshListenable: _authRefresh,
  redirect: (context, state) {
    try {
      final container = ProviderScope.containerOf(context, listen: false);
      final auth = container.read(authProvider);
      final authState = auth.valueOrNull;
      final loc = state.matchedLocation;

      if (loc == '/fake-download') return null;

      if (authState == null || !authState.authenticated) {
        return '/dashboard';
      }

      if (loc == '/signup') {
        return '/dashboard';
      }
    } catch (_) {}
    return null;
  },
  routes: [
    GoRoute(
      path: '/fake-download',
      name: 'fake-download',
      builder: (context, state) => const FakeDownloadScreen(),
    ),
    GoRoute(
      path: '/signup',
      name: 'signup',
      builder: (context, state) => const SignupScreen(),
    ),
    GoRoute(
      path: '/onboarding',
      name: 'onboarding',
      builder: (context, state) => const ProfileOnboardingScreen(),
    ),
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) {
        return DashboardShell(navigationShell: navigationShell);
      },
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/dashboard',
              name: 'dashboard',
              builder: (context, state) => const DashboardScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/universities',
              name: 'universities',
              builder: (context, state) => const UniversitiesScreen(),
              routes: [
                GoRoute(
                  path: ':id',
                  name: 'university-detail',
                  builder: (context, state) => UniversityDetailScreen(
                    universityId: state.pathParameters['id']!,
                  ),
                  routes: [
                    GoRoute(
                      path: 'helper',
                      name: 'application-helper',
                      builder: (context, state) => ApplicationHelperScreen(
                        universityName: state.uri.queryParameters['name'] ?? 'University',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/applications',
              name: 'applications',
              builder: (context, state) => const ApplicationTrackerScreen(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/funding',
              name: 'funding',
              builder: (context, state) => const FundingListScreen(),
              routes: [
                GoRoute(
                  path: ':id',
                  name: 'funding-detail',
                  builder: (context, state) => FundingDetailScreen(
                    bursaryId: state.pathParameters['id']!,
                  ),
                ),
              ],
            ),
          ],
        ),
      ],
    ),
    GoRoute(
      path: '/aps-calculator',
      name: 'aps-calculator',
      builder: (context, state) => const ApsCalculatorScreen(),
    ),
    GoRoute(
      path: '/ai-recommendations',
      name: 'ai-recommendations',
      builder: (context, state) => const AiRecommendationsScreen(),
    ),
    GoRoute(
      path: '/notifications',
      name: 'notifications',
      builder: (context, state) => const NotificationsScreen(),
    ),
    GoRoute(
      path: '/chat',
      name: 'chat',
      builder: (context, state) => const ChatScreen(),
    ),
    GoRoute(
      path: '/settings',
      name: 'settings',
      builder: (context, state) => const SettingsScreen(),
    ),
    GoRoute(
      path: '/privacy',
      name: 'privacy',
      builder: (context, state) => const PrivacyScreen(),
    ),
  ],
);

class DashboardShell extends ConsumerWidget {
  final StatefulNavigationShell navigationShell;
  const DashboardShell({super.key, required this.navigationShell});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sidebarPos = ref.watch(sidebarProvider);
    final currentIndex = navigationShell.currentIndex;
    final isRight = sidebarPos == SidebarPosition.right;

    return Scaffold(
      drawer: isRight ? null : _buildDrawer(context, ref, currentIndex),
      endDrawer: isRight ? _buildDrawer(context, ref, currentIndex) : null,
      body: Stack(
        children: [
          navigationShell,
          if (currentIndex != 0)
            Positioned(
              right: 16,
              bottom: 80,
              child: GestureDetector(
                onTap: () => context.push('/ai-recommendations'),
                child: const StarAvatar(size: 40, pulse: true),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildDrawer(BuildContext context, WidgetRef ref, int currentIndex) {
    final navItems = [
      _NavItemData(icon: Icons.home_rounded, label: 'Home', route: '/dashboard', index: 0),
      _NavItemData(icon: Icons.person_rounded, label: 'My Profile', route: '/onboarding'),
      _NavItemData(icon: Icons.notifications_rounded, label: 'Notifications', route: '/notifications'),
      _NavItemData(icon: Icons.auto_awesome_rounded, label: 'Advisor', route: '/ai-recommendations'),
      _NavItemData(icon: Icons.account_balance_wallet_rounded, label: 'Funding', route: '/funding', index: 3),
      _NavItemData(icon: Icons.school_rounded, label: 'Universities', route: '/universities', index: 1),
      _NavItemData(icon: Icons.assignment_rounded, label: 'Applications', route: '/applications', index: 2),
      _NavItemData(icon: Icons.chat_rounded, label: 'Community', route: '/chat'),
      _NavItemData(icon: Icons.settings_rounded, label: 'Settings', route: '/settings'),
    ];

    return Drawer(
      backgroundColor: AppColors.surface,
      width: 260,
      child: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 24, 16, 16),
              child: Row(
                children: [
                  Text(
                    'StudentSync',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                      letterSpacing: -0.5,
                    ),
                  ),
                  Text(
                    'SA',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: AppColors.accent,
                      letterSpacing: -0.5,
                    ),
                  ),
                ],
              ),
            ),
            const Divider(color: AppColors.divider, thickness: 1),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: navItems.map((item) {
                  final isSelected = item.index != null
                      ? currentIndex == item.index
                      : item.route == '/dashboard'
                          ? currentIndex == 0
                          : false;
                  return _SidebarItem(
                    icon: item.icon,
                    label: item.label,
                    selected: isSelected,
                    onTap: () {
                      Navigator.of(context).pop();
                      if (item.index != null) {
                        navigationShell.goBranch(item.index!,
                            initialLocation: currentIndex == item.index);
                      } else {
                        context.push(item.route);
                      }
                    },
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavItemData {
  final IconData icon;
  final String label;
  final String route;
  final int? index;
  const _NavItemData({
    required this.icon,
    required this.label,
    required this.route,
    this.index,
  });
}

class _SidebarItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _SidebarItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: selected ? AppColors.primary.withValues(alpha: 0.15) : Colors.transparent,
              borderRadius: BorderRadius.circular(12),
              border: selected ? Border.all(color: AppColors.primary.withValues(alpha: 0.3)) : null,
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  size: 22,
                  color: selected ? AppColors.primary : AppColors.textMuted,
                ),
                const SizedBox(width: 14),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                    color: selected ? AppColors.primary : AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
