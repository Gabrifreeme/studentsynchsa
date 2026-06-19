import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/domain/repositories/profile_repository.dart';

class ProfileNotifier extends StateNotifier<AsyncValue<StudentProfile?>> {
  late final ProfileRepository _repo;

  ProfileNotifier() : super(const AsyncLoading()) {
    _repo = ProfileRepositoryImpl();
    _init();
  }

  Future<void> _init() async {
    try {
      var profile = await _repo.getProfile();
      if (profile == null) {
        // autoLogin() might still be creating the profile — wait and retry
        await Future.delayed(const Duration(milliseconds: 800));
        profile = await _repo.getProfile();
      }
      state = AsyncData(profile);
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
    }
  }

  Future<void> saveProfile(StudentProfile profile) async {
    try {
      await _repo.saveProfile(profile);
      state = AsyncData(profile);
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
      rethrow;
    }
  }

  Future<void> updateProfile(StudentProfile profile) async {
    await _repo.updateProfile(profile);
    state = AsyncData(profile);
  }

  Future<void> deleteProfile() async {
    await _repo.deleteProfile();
    state = const AsyncData(null);
  }
}

final profileProvider = StateNotifierProvider<ProfileNotifier, AsyncValue<StudentProfile?>>((ref) {
  return ProfileNotifier();
});
