import 'package:google_sign_in/google_sign_in.dart';
import 'package:uuid/uuid.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/domain/repositories/auth_repository.dart';

class AuthService implements AuthRepository {
  GoogleSignIn? _googleSignIn;
  final _profileRepo = ProfileRepositoryImpl();

  AuthService() {
    try {
      _googleSignIn = GoogleSignIn(
        scopes: ['email'],
        clientId: '864470911027-46ogt1qabojutsfp698rr5kvs4acudl4.apps.googleusercontent.com',
      );
    } catch (_) {}
  }

  @override
  Future<AuthResult> signInWithEmail(String email, String password) async {
    try {
      final storedEmail = HiveDatabase.settings.get('auth_email') ?? '';
      final storedPassword = HiveDatabase.settings.get('auth_password') ?? '';

      // If credentials exist, verify against them
      if (storedEmail.isNotEmpty && storedPassword.isNotEmpty) {
        if (storedEmail != email || storedPassword != password) {
          return const AuthResult(success: false, error: 'Invalid email or password');
        }
      } else {
        // No stored credentials — likely signed out before the fix that
        // stopped deleting them. Check if a profile with this email exists.
        final profile = await _profileRepo.getProfile();
        if (profile == null || profile.contact.email != email) {
          return const AuthResult(success: false, error: 'No account found — sign up first');
        }
        // Recreate auth data so future sign-ins use stored credentials
        await _setAuthData(email: email, id: profile.id, password: password);
      }

      final userId = HiveDatabase.settings.get('auth_user_id');
      if (userId == null || userId.isEmpty) {
        final fallbackId = email.hashCode.toString();
        await HiveDatabase.settings.put('auth_user_id', fallbackId);
      }
      final existingProfile = await _profileRepo.getProfile();
      return AuthResult(
        success: true,
        profile: existingProfile ?? StudentProfile(
          id: userId ?? email.hashCode.toString(),
          contact: ContactInfo(email: email),
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
      await _setAuthData(email: email, id: id, password: password);
      return AuthResult(
        success: true,
        profile: StudentProfile(id: id, contact: ContactInfo(email: email)),
      );
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }

  @override
  Future<AuthResult> signInWithGoogle() async {
    try {
      if (_googleSignIn == null) {
        return const AuthResult(success: false, error: 'Google Sign-In not available on web');
      }
      final account = await _googleSignIn?.signIn();
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
      await _setAuthData(email: email, id: id);
      return AuthResult(
        success: true,
        profile: StudentProfile(
          id: id,
          personal: PersonalDetails(firstName: firstName, lastName: lastName),
          contact: ContactInfo(email: email),
        ),
      );
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }

  @override
  Future<AuthResult> signInWithApple() async {
    return const AuthResult(
      success: false,
      error: 'Apple login requires Apple Developer Program — coming soon',
    );
  }

  @override
  Future<void> signOut() async {
    try {
      await _googleSignIn?.signOut();
    } catch (_) {}
    await HiveDatabase.settings.delete('auth_user_id');
  }

  @override
  Future<bool> isSignedIn() async {
    final userId = HiveDatabase.settings.get('auth_user_id');
    return userId != null && userId.isNotEmpty;
  }

  @override
  Future<String?> getCurrentUserId() async {
    return HiveDatabase.settings.get('auth_user_id');
  }

  Future<void> _setAuthData({required String email, required String id, String? password}) async {
    await HiveDatabase.settings.put('auth_email', email);
    await HiveDatabase.settings.put('auth_user_id', id);
    if (password != null) {
      await HiveDatabase.settings.put('auth_password', password);
    }
  }

  @override
  Future<AuthResult> autoLogin() async {
    try {
      var profile = await _profileRepo.getProfile();
      final existingId = profile?.id ?? const Uuid().v4();
      profile = StudentProfile(
          id: existingId,
          onboardingComplete: true,
          personal: PersonalDetails(
            title: 'Mr',
            initials: 'T',
            firstName: 'Test',
            lastName: 'User',
            gender: 'Male',
            dateOfBirth: DateTime(1964, 4, 13),
            idNumber: '6404135555555',
          ),
          contact: ContactInfo(
            email: 'test.user@example.com',
            phone: '0712345678',
          ),
          address: AddressInfo(
            address: '123 Test Street',
            addressLine2: 'Test Suburb',
            province: 'Gauteng',
            postalCode: '2000',
          ),
          demographic: DemographicInfo(
            nationality: 'RSA',
            countryOfBirth: 'South Africa',
            homeLanguage: 'English',
            populationGroup: 'Black',
            maritalStatus: 'Single',
          ),
          status: StatusInfo(
            disabilityStatus: 'No',
            bursaryRequired: 'Yes',
            employmentStatus: 'Studying at school',
          ),
          school: SchoolInfo(
            schoolName: 'Test High School',
            currentGrade: 'Grade 12',
            currentlyDoing: 'Studying at school',
          ),
          nextOfKin: NextOfKin(
            name: 'Parent Test',
            mobilePhone: '0712345679',
            homePhone: '0211234567',
            addressLine1: '123 Test Street',
            addressLine2: 'Test Suburb',
            postalCode: '2000',
            email: 'parent@example.com',
          ),
          accountContact: AccountContact(
            name: 'Account Contact',
            mobilePhone: '0723456789',
            homePhone: '0217654321',
            addressLine1: '456 Account Street',
            addressLine2: 'Account Suburb',
            postalCode: '2001',
            email: 'account@example.com',
          ),
          results: ResultsInfo(
            matricYear: DateTime.now().year - 1,
            applicationLevel: 'Undergraduate',
            upgrading: 'No',
            matricType: 'South African',
            examinationNumber: '1234567890',
            schoolLeavingCertificate: 'GRADE 12',
          ),
          qualification: QualificationInfo(
            academicYear: DateTime.now().year,
            applicationPeriod: '1ST YEAR',
            studyMode: 'FULL-TIME',
            studyTiming: 'Full-Time',
            choices: [
              QualificationChoice(faculty: 'Science', programme: 'Computer Science'),
            ],
          ),
          agreement: AgreementInfo(
            acceptanceStatus: 'Accepted',
          ),
        );
        await _profileRepo.saveProfile(profile);
      if (HiveDatabase.settings.get('auth_user_id') == null || 
          (HiveDatabase.settings.get('auth_user_id') ?? '').isEmpty) {
        await _setAuthData(email: profile.contact.email, id: profile.id);
      }
      return AuthResult(success: true, profile: profile);
    } catch (e) {
      return AuthResult(success: false, error: e.toString());
    }
  }
}
