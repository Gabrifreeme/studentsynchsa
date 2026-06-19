import 'package:studentsyncsa/domain/models/university.dart';

abstract class UniversityRepository {
  Future<List<University>> getUniversities();
  Future<University?> getUniversityById(String id);
  Future<void> cacheUniversities(List<University> universities);
}
