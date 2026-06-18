import 'dart:convert';
import 'package:studentsynchsa/data/datasources/local/hive_database.dart';
import 'package:studentsynchsa/domain/models/student_profile.dart';
import 'package:studentsynchsa/domain/repositories/profile_repository.dart';

class ProfileRepositoryImpl implements ProfileRepository {
  @override
  Future<StudentProfile?> getProfile() async {
    final raw = HiveDatabase.profile.get('profile');
    if (raw == null || raw.isEmpty) return null;
    try {
      return StudentProfile.fromJson(jsonDecode(raw));
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> saveProfile(StudentProfile profile) async {
    await HiveDatabase.profile.put('profile', jsonEncode(profile.toJson()));
    await HiveDatabase.settings.put('last_sync', DateTime.now().toIso8601String());
  }

  @override
  Future<void> updateProfile(StudentProfile profile) async {
    await saveProfile(profile);
  }

  @override
  Future<void> deleteProfile() async {
    await HiveDatabase.profile.delete('profile');
  }

  @override
  Future<bool> hasProfile() async {
    return HiveDatabase.profile.containsKey('profile');
  }

  @override
  Stream<StudentProfile?> watchProfile() {
    return HiveDatabase.profile.watch().map((_) {
      final raw = HiveDatabase.profile.get('profile');
      if (raw == null || raw.isEmpty) return null;
      try {
        return StudentProfile.fromJson(jsonDecode(raw));
      } catch (_) {
        return null;
      }
    });
  }
}
