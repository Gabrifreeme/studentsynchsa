import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:uuid/uuid.dart';
import 'package:studentsynchsa/domain/models/student_profile.dart';
import 'package:studentsynchsa/domain/repositories/auth_repository.dart';

class AuthService implements AuthRepository {
  final FlutterSecureStorage _secureStorage;
  final GoogleSignIn _googleSignIn;

  AuthService()
      : _secureStorage = const FlutterSecureStorage(),
        _googleSignIn = GoogleSignIn(
          scopes: ['email'],
          clientId: '864470911027-46ogt1qabojutsfp698rr5kvs4acudl4.apps.googleusercontent.com',
        );

  @override
  Future<AuthResult> signInWithEmail(String email, String password) async {
    try {
      // MVP: mock authentication — stores locally
      await _secureStorage.write(key: 'user_email', value: email);
      await _secureStorage.write(key: 'user_password', value: password);
      await _secureStorage.write(key: 'user_id', value: email.hashCode.toString());
      return AuthResult(
        success: true,
        profile: StudentProfile(
          id: email.hashCode.toString(),
          email: email,
        ),
      );
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }

  @override
  Future<AuthResult> signUpWithEmail(String email, String password) async {
    try {
      final id = const Uuid().v4();
      await _secureStorage.write(key: 'user_email', value: email);
      await _secureStorage.write(key: 'user_password', value: password);
      await _secureStorage.write(key: 'user_id', value: id);
      return AuthResult(
        success: true,
        profile: StudentProfile(id: id, email: email),
      );
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }

  @override
  Future<AuthResult> signInWithGoogle() async {
    try {
      final account = await _googleSignIn.signIn();
      if (account == null) {
        return const AuthResult(success: false, error: 'cancelled');
      }
      final id = account.id;
      final email = account.email;
      final firstName = account.displayName?.split(' ').first ?? '';
      final nameParts = account.displayName?.split(' ') ?? [];
      final lastName = nameParts.length > 1
          ? nameParts.skip(1).join(' ')
          : '';
      await _secureStorage.write(key: 'user_email', value: email);
      await _secureStorage.write(key: 'user_id', value: id);
      return AuthResult(
        success: true,
        profile: StudentProfile(
          id: id,
          email: email,
          firstName: firstName,
          lastName: lastName,
        ),
      );
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }

  @override
  Future<AuthResult> signInWithApple() async {
    // Apple Sign-In requires Apple Developer Program ($99/yr)
    return const AuthResult(
      success: false,
      error: 'Apple login requires Apple Developer Program — coming soon',
    );
  }

  @override
  Future<void> signOut() async {
    await _googleSignIn.signOut();
    await _secureStorage.deleteAll();
  }

  @override
  Future<bool> isSignedIn() async {
    final userId = await _secureStorage.read(key: 'user_id');
    return userId != null && userId.isNotEmpty;
  }

  @override
  Future<String?> getCurrentUserId() async {
    return await _secureStorage.read(key: 'user_id');
  }
}
