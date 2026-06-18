import 'package:studentsynchsa/domain/models/student_profile.dart';

abstract class ProfileRepository {
  Future<StudentProfile?> getProfile();
  Future<void> saveProfile(StudentProfile profile);
  Future<void> updateProfile(StudentProfile profile);
  Future<void> deleteProfile();
  Future<bool> hasProfile();
  Stream<StudentProfile?> watchProfile();
}
