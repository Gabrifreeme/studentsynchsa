import 'dart:convert';
import 'package:studentsynchsa/core/constants/app_constants.dart';
import 'package:studentsynchsa/data/datasources/local/hive_database.dart';
import 'package:studentsynchsa/data/datasources/mock_university_data.dart';
import 'package:studentsynchsa/domain/models/university.dart';
import 'package:studentsynchsa/domain/repositories/university_repository.dart';

class UniversityRepositoryImpl implements UniversityRepository {
  @override
  Future<List<University>> getUniversities() async {
    final cached = HiveDatabase.universities.get('all');
    if (cached != null && cached.isNotEmpty) {
      try {
        final list = jsonDecode(cached) as List;
        return list.map((e) => University.fromJson(e)).toList();
      } catch (_) {}
    }
    return MockUniversityData.all;
  }

  @override
  Future<University?> getUniversityById(String id) async {
    final cached = MockUniversityData.getById(id);
    if (cached != null) return cached;
    final all = await getUniversities();
    try {
      return all.firstWhere((u) => u.id == id);
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> cacheUniversities(List<University> universities) async {
    final json = jsonEncode(universities.map((u) => u.toJson()).toList());
    await HiveDatabase.universities.put('all', json);
  }
}
