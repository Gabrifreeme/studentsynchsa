import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsynchsa/core/router/app_router.dart';
import 'package:studentsynchsa/domain/models/student_profile.dart';
import 'package:studentsynchsa/domain/repositories/auth_repository.dart';
import 'package:studentsynchsa/domain/repositories/profile_repository.dart';
import 'package:studentsynchsa/services/auth_service.dart';
import 'package:studentsynchsa/data/repositories/profile_repository_impl.dart';

class AuthState {
  final bool authenticated;
  final StudentProfile? profile;
  final bool isNewUser;

  const AuthState({
    this.authenticated = false,
    this.profile,
    this.isNewUser = false,
  });
}

class AuthNotifier extends StateNotifier<AsyncValue<AuthState>> {
  late final AuthRepository _authService;
  late final ProfileRepository _profileRepo;

  AuthNotifier() : super(const AsyncData(AuthState())) {
    _authService = AuthService();
    _profileRepo = ProfileRepositoryImpl();
    _init();
  }

  Future<void> _init() async {
    try {
      final result = await _authService.autoLogin();
      if (result.success && result.profile != null) {
        state = AsyncData(AuthState(authenticated: true, profile: result.profile));
      }
    } catch (_) {}
    triggerAuthRedirect();
  }

  Future<String?> signInWithEmail(String email, String password) async {
    try {
      final result = await _authService.signInWithEmail(email, password);
      if (result.success) {
        if (result.profile != null) {
          try {
            await _profileRepo.saveProfile(result.profile!);
          } catch (_) {}
        }
        state = AsyncData(AuthState(authenticated: true, profile: result.profile));
      }
      triggerAuthRedirect();
      return result.error;
    } catch (e) {
      triggerAuthRedirect();
      return e.toString();
    }
  }

  Future<String?> signUpWithEmail(String email, String password) async {
    try {
      final result = await _authService.signUpWithEmail(email, password);
      if (result.success) {
        if (result.profile != null) {
          try {
            await _profileRepo.saveProfile(result.profile!);
          } catch (_) {}
        }
        state = AsyncData(AuthState(
          authenticated: true,
          profile: result.profile,
          isNewUser: true,
        ));
      }
      triggerAuthRedirect();
      return result.error;
    } catch (e) {
      triggerAuthRedirect();
      return e.toString();
    }
  }

  Future<String?> signInWithGoogle() async {
    try {
      final result = await _authService.signInWithGoogle();
      if (result.success) {
        if (result.profile != null) {
          try {
            final existing = await _profileRepo.getProfile();
            if (existing != null) {
              final merged = result.profile!.copyWith(
                personal: existing.personal.copyWith(
                  firstName: existing.personal.firstName.isNotEmpty ? existing.personal.firstName : null,
                  lastName: existing.personal.lastName.isNotEmpty ? existing.personal.lastName : null,
                ),
                contact: existing.contact.copyWith(
                  phone: existing.contact.phone.isNotEmpty ? existing.contact.phone : null,
                ),
              );
              await _profileRepo.saveProfile(merged);
            } else {
              await _profileRepo.saveProfile(result.profile!);
            }
          } catch (_) {}
        }
        state = AsyncData(AuthState(authenticated: true, profile: result.profile));
      }
      triggerAuthRedirect();
      return result.error;
    } catch (e) {
      triggerAuthRedirect();
      return e.toString();
    }
  }

  Future<void> signOut() async {
    try {
      await _authService.signOut();
    } catch (_) {}
    state = const AsyncData(AuthState());
    triggerAuthRedirect();
  }

  void completeOnboarding(StudentProfile profile) {
    final updated = profile.copyWith(onboardingComplete: true);
    state = AsyncData(AuthState(authenticated: true, profile: updated, isNewUser: false));
    try {
      _profileRepo.saveProfile(updated);
    } catch (_) {}
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AsyncValue<AuthState>>((ref) {
  return AuthNotifier();
});
