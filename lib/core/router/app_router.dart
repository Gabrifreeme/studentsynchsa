import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/presentation/providers/auth_provider.dart';
import 'package:studentsynchsa/presentation/screens/auth/signup_screen.dart';
import 'package:studentsynchsa/presentation/screens/dashboard/dashboard_screen.dart';
import 'package:studentsynchsa/presentation/screens/profile/profile_onboarding_screen.dart';
import 'package:studentsynchsa/presentation/screens/universities/universities_screen.dart';
import 'package:studentsynchsa/presentation/screens/universities/university_detail_screen.dart';
import 'package:studentsynchsa/presentation/screens/aps/aps_calculator_screen.dart';
import 'package:studentsynchsa/presentation/screens/applications/application_tracker_screen.dart';
import 'package:studentsynchsa/presentation/screens/funding/funding_list_screen.dart';
import 'package:studentsynchsa/presentation/screens/funding/funding_detail_screen.dart';
import 'package:studentsynchsa/presentation/screens/ai_recommendations/ai_recommendations_screen.dart';
import 'package:studentsynchsa/presentation/screens/notifications/notifications_screen.dart';
import 'package:studentsynchsa/presentation/screens/chat/chat_screen.dart';
import 'package:studentsynchsa/presentation/screens/settings/settings_screen.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';

final GlobalKey<NavigatorState> _rootNavigator = GlobalKey<NavigatorState>();

final _authRefresh = ValueNotifier<int>(0);

void triggerAuthRedirect() {
  _authRefresh.value++;
}

final appRouter = GoRouter(
  navigatorKey: _rootNavigator,
  initialLocation: '/dashboard',
  refreshListenable: _authRefresh,
  redirect: (context, state) {
    try {
      final container = ProviderScope.containerOf(context, listen: false);
      final auth = container.read(authProvider);
      final authState = auth.valueOrNull;
      final loc = state.matchedLocation;

      if (authState == null || !authState.authenticated) {
        // Should never happen now — autoLogin creates anonymous profile
        return '/dashboard';
      }

      // Always go to dashboard, no login/signup gate
      if (loc == '/signup') {
        return '/dashboard';
      }
    } catch (_) {}
    return null;
  },
  routes: [
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
                    initialTab: state.uri.queryParameters['tab'] ?? '',
                  ),
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
  ],
);

class DashboardShell extends StatefulWidget {
  final StatefulNavigationShell navigationShell;
  const DashboardShell({super.key, required this.navigationShell});

  @override
  State<DashboardShell> createState() => _DashboardShellState();
}

class _DashboardShellState extends State<DashboardShell>
    with SingleTickerProviderStateMixin {
  late AnimationController _floatCtrl;
  late Animation<double> _floatAnim;

  @override
  void initState() {
    super.initState();
    _floatCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _floatAnim = Tween<double>(begin: -6, end: 6).animate(
      CurvedAnimation(parent: _floatCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _floatCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final currentIndex = widget.navigationShell.currentIndex;
    return Scaffold(
      body: Stack(
        children: [
          widget.navigationShell,
          if (currentIndex != 0)
            Positioned(
            right: 16,
            bottom: 80,
            child: GestureDetector(
              onTap: () => context.push('/ai-recommendations'),
              child: AnimatedBuilder(
                animation: _floatAnim,
                builder: (context, child) {
                  return Transform.translate(
                    offset: Offset(0, _floatAnim.value),
                    child: child,
                  );
                },
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.starGold.withValues(alpha: 0.3),
                        blurRadius: 8,
                        spreadRadius: 1,
                      ),
                    ],
                  ),
                  child: const StarAvatar(size: 40, pulse: true),
                ),
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          widget.navigationShell.goBranch(
            index,
            initialLocation: index == widget.navigationShell.currentIndex,
          );
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.school_outlined),
            selectedIcon: Icon(Icons.school_rounded),
            label: 'Universities',
          ),
          NavigationDestination(
            icon: Icon(Icons.assignment_outlined),
            selectedIcon: Icon(Icons.assignment_rounded),
            label: 'Applications',
          ),
          NavigationDestination(
            icon: Icon(Icons.account_balance_outlined),
            selectedIcon: Icon(Icons.account_balance_rounded),
            label: 'Funding',
          ),
        ],
      ),
    );
  }
}
