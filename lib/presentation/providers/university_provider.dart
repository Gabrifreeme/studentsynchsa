import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsynchsa/data/repositories/university_repository_impl.dart';
import 'package:studentsynchsa/domain/models/university.dart';
import 'package:studentsynchsa/domain/repositories/university_repository.dart';

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
