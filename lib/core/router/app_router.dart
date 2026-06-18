import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsynchsa/presentation/screens/auth/login_screen.dart';
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

final GlobalKey<NavigatorState> _rootNavigator = GlobalKey<NavigatorState>();

final appRouter = GoRouter(
  navigatorKey: _rootNavigator,
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      name: 'login',
      builder: (context, state) => const LoginScreen(),
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

class DashboardShell extends StatelessWidget {
  final StatefulNavigationShell navigationShell;
  const DashboardShell({super.key, required this.navigationShell});

  @override
  Widget build(BuildContext context) {
    final currentIndex = navigationShell.currentIndex;
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          navigationShell.goBranch(
            index,
            initialLocation: index == navigationShell.currentIndex,
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
