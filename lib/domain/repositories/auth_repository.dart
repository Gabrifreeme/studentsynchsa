import 'package:studentsynchsa/domain/models/student_profile.dart';

abstract class AuthRepository {
  Future<AuthResult> signInWithEmail(String email, String password);
  Future<AuthResult> signUpWithEmail(String email, String password);
  Future<AuthResult> signInWithGoogle();
  Future<AuthResult> signInWithApple();
  Future<void> signOut();
  Future<bool> isSignedIn();
  Future<String?> getCurrentUserId();
  Future<AuthResult> autoLogin();
}

class AuthResult {
  final bool success;
  final String? error;
  final StudentProfile? profile;

  const AuthResult({required this.success, this.error, this.profile});
}
