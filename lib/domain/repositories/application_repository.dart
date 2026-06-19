import 'package:studentsyncsa/domain/models/application.dart';
import 'package:studentsyncsa/domain/models/bursary.dart';

abstract class ApplicationRepository {
  Future<List<UniversityApplication>> getApplications();
  Future<void> saveApplication(UniversityApplication application);
  Future<void> updateApplication(UniversityApplication application);
  Future<void> deleteApplication(String id);
  Stream<List<UniversityApplication>> watchApplications();

  Future<List<BursaryApplication>> getBursaryApplications();
  Future<void> saveBursaryApplication(BursaryApplication application);
  Future<void> updateBursaryApplication(BursaryApplication application);
  Future<void> deleteBursaryApplication(String id);
}
