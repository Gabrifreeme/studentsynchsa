import 'package:flutter_riverpod/flutter_riverpod.dart';
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

  AuthNotifier() : super(const AsyncLoading()) {
    _authService = AuthService();
    _profileRepo = ProfileRepositoryImpl();
    _init();
  }

  Future<void> _init() async {
    try {
      final signedIn = await _authService.isSignedIn();
      if (signedIn) {
        final profile = await _profileRepo.getProfile();
        state = AsyncData(AuthState(authenticated: true, profile: profile));
      } else {
        state = const AsyncData(AuthState());
      }
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
    }
  }

  Future<String?> signInWithEmail(String email, String password) async {
    final result = await _authService.signInWithEmail(email, password);
    if (result.success) {
      if (result.profile != null) {
        await _profileRepo.saveProfile(result.profile!);
      }
      state = AsyncData(AuthState(authenticated: true, profile: result.profile));
    }
    return result.error;
  }

  Future<String?> signUpWithEmail(String email, String password) async {
    final result = await _authService.signUpWithEmail(email, password);
    if (result.success) {
      if (result.profile != null) {
        await _profileRepo.saveProfile(result.profile!);
      }
      state = AsyncData(AuthState(
        authenticated: true,
        profile: result.profile,
        isNewUser: true,
      ));
    }
    return result.error;
  }

  Future<String?> signInWithGoogle() async {
    final result = await _authService.signInWithGoogle();
    if (result.success) {
      if (result.profile != null) {
        final existing = await _profileRepo.getProfile();
        if (existing != null) {
          final merged = result.profile!.copyWith(
            firstName: existing.firstName.isNotEmpty ? existing.firstName : null,
            lastName: existing.lastName.isNotEmpty ? existing.lastName : null,
            phone: existing.phone.isNotEmpty ? existing.phone : null,
          );
          await _profileRepo.saveProfile(merged);
        } else {
          await _profileRepo.saveProfile(result.profile!);
        }
      }
      state = AsyncData(AuthState(authenticated: true, profile: result.profile));
    }
    return result.error;
  }

  Future<void> signOut() async {
    await _authService.signOut();
    state = const AsyncData(AuthState());
  }

  void completeOnboarding(StudentProfile profile) {
    final updated = profile.copyWith(onboardingComplete: true);
    state = AsyncData(AuthState(authenticated: true, profile: updated, isNewUser: false));
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AsyncValue<AuthState>>((ref) {
  return AuthNotifier();
});
