import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/data/repositories/university_repository_impl.dart';
import 'package:studentsyncsa/domain/models/university.dart';
import 'package:studentsyncsa/domain/repositories/university_repository.dart';

class UniversitiesNotifier extends StateNotifier<AsyncValue<List<University>>> {
  late final UniversityRepository _repo;

  UniversitiesNotifier() : super(const AsyncLoading()) {
    _repo = UniversityRepositoryImpl();
    _init();
  }

  Future<void> _init() async {
    try {
      final universities = await _repo.getUniversities();
      state = AsyncData(universities);
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
    }
  }

  Future<University?> getById(String id) => _repo.getUniversityById(id);
}

final universitiesProvider = StateNotifierProvider<UniversitiesNotifier, AsyncValue<List<University>>>((ref) {
  return UniversitiesNotifier();
});
