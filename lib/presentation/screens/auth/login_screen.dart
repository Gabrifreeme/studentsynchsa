import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _obscurePassword = true;
  bool _loading = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  /// A returning student may have a saved Hive profile even when the auth
  /// provider has not loaded it yet. Check both before choosing the route.
  Future<void> _routeAfterLogin() async {
    var complete =
        ref.read(authProvider).valueOrNull?.profile?.onboardingComplete == true;
    if (!complete) {
      try {
        final saved = await ProfileRepositoryImpl().getProfile();
        complete = saved != null &&
            (saved.onboardingComplete || saved.personal.firstName.isNotEmpty);
      } catch (_) {}
    }
    if (!mounted) return;
    context.go(complete ? '/dashboard' : '/onboarding');
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final error = await ref.read(authProvider.notifier).signInWithEmail(
            _emailCtrl.text.trim(),
            _passwordCtrl.text,
          );
      if (error != null && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error), backgroundColor: AppColors.error),
        );
      } else if (mounted) {
        await _routeAfterLogin();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loginWithGoogle() async {
    setState(() => _loading = true);
    try {
      final error = await ref.read(authProvider.notifier).signInWithGoogle();
      if (error != null && error != 'cancelled' && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error), backgroundColor: AppColors.error),
        );
      } else if (mounted) {
        await _routeAfterLogin();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final cardWidth = size.width > 400 ? 380.0 : size.width * 0.92;
    final isShort = size.height < 700;

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              child: SizedBox(
                width: cardWidth,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(height: isShort ? 8 : 24),
                    // Star + Branding
                    StarAvatar(size: isShort ? 48 : 64, pulse: true),
                    SizedBox(height: isShort ? 8 : 16),
                    Text(
                      'LibSyncStudent',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: isShort ? 22 : 26,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Powered by ACEsi',
                      style: const TextStyle(
                        color: AppColors.starGold,
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    SizedBox(height: isShort ? 16 : 24),

                    // Login Card
                    AppCard(
                      padding: EdgeInsets.all(isShort ? 16 : 24),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Text(
                              'Welcome Back',
                              style: TextStyle(
                                color: AppColors.textPrimary,
                                fontSize: isShort ? 18 : 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 3),
                            const Text(
                              'Sign in to continue',
                              style: TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 10,
                              ),
                            ),
                            SizedBox(height: isShort ? 12 : 20),
                            TextFormField(
                              controller: _emailCtrl,
                              keyboardType: TextInputType.emailAddress,
                              decoration: const InputDecoration(
                                labelText: 'Email',
                                prefixIcon: const StarIcon(Icons.email_outlined),
                              ),
                              validator: (v) =>
                                  v?.isEmpty == true ? 'Enter your email' : null,
                            ),
                            SizedBox(height: isShort ? 8 : 14),
                            TextFormField(
                              controller: _passwordCtrl,
                              obscureText: _obscurePassword,
                              decoration: InputDecoration(
                                labelText: 'Password',
                                prefixIcon: const StarIcon(Icons.lock_outlined),
                                suffixIcon: IconButton(
                                  icon: StarIcon(
                                    _obscurePassword
                                                                            ? Icons.visibility_off_outlined
                                                                            : Icons.visibility_outlined,
                                  ),
                                  onPressed: () => setState(
                                      () => _obscurePassword = !_obscurePassword),
                                ),
                              ),
                              validator: (v) =>
                                  v?.isEmpty == true ? 'Enter your password' : null,
                            ),
                            const SizedBox(height: 6),
                            Align(
                              alignment: Alignment.centerRight,
                              child: TextButton(
                                onPressed: () {},
                                child: const Text('Forgot password?'),
                              ),
                            ),
                            SizedBox(height: isShort ? 8 : 14),
                            SizedBox(
                              height: 44,
                              child: ElevatedButton(
                                onPressed: _loading ? null : _login,
                                child: _loading
                                    ? const SizedBox(
                                        width: 20,
                                        height: 20,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          color: AppColors.background,
                                        ),
                                      )
                                    : const Text('Login'),
                              ),
                            ),
                            SizedBox(height: isShort ? 8 : 14),
                            Row(
                              children: [
                                const Expanded(child: Divider()),
                                Padding(
                                  padding:
                                      const EdgeInsets.symmetric(horizontal: 16),
                                  child: Text(
                                    'or',
                                    style: TextStyle(
                                      color: AppColors.textMuted,
                                      fontSize: 9,
                                    ),
                                  ),
                                ),
                                const Expanded(child: Divider()),
                              ],
                            ),
                            SizedBox(height: isShort ? 8 : 14),
                            SizedBox(
                              height: 42,
                              child: OutlinedButton.icon(
                                onPressed: _loading ? null : _loginWithGoogle,
                                icon: Image.asset('assets/icons/google_g.png',
                                    width: 24, height: 24),
                                label: const Text('Sign in with Google'),
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: AppColors.textPrimary,
                                  side: const BorderSide(color: AppColors.border),
                                ),
                              ),
                            ),
                            // Apple sign-in parked until an Apple Developer
                            // account is set up. Restore this block later.
                            // const SizedBox(height: 6),
                            // SizedBox(
                            //   height: 42,
                            //   child: OutlinedButton.icon(
                            //     onPressed: () {
                            //       ScaffoldMessenger.of(context).showSnackBar(
                            //         const SnackBar(
                            //           content: Text(
                            //             'Apple login requires Apple Developer Program — coming soon',
                            //           ),
                            //         ),
                            //       );
                            //     },
                            //     icon: const Icon(Icons.apple_rounded,
                            //         size: 24, color: AppColors.info),
                            //     label: const Text('Sign in with Apple'),
                            //     style: OutlinedButton.styleFrom(
                            //       foregroundColor: AppColors.textMuted,
                            //       side: const BorderSide(color: AppColors.border),
                            //     ),
                            //   ),
                            // ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 11),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text(
                          "Don't have an account? ",
                          style: TextStyle(color: AppColors.textSecondary),
                        ),
                        GestureDetector(
                          onTap: () => context.push('/signup'),
                          child: const Text(
                            'Sign Up',
                            style: TextStyle(
                              color: AppColors.primaryLight,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    SizedBox(height: isShort ? 8 : 16),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
