import 'dart:convert';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/domain/models/application.dart';
import 'package:studentsyncsa/domain/models/bursary.dart';
import 'package:studentsyncsa/domain/repositories/application_repository.dart';

class ApplicationRepositoryImpl implements ApplicationRepository {
  @override
  Future<List<UniversityApplication>> getApplications() async {
    final raw = HiveDatabase.applications.get('university_apps');
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List;
      return list.map((e) => UniversityApplication.fromJson(e)).toList();
    } catch (_) {
      return [];
    }
  }

  @override
  Future<void> saveApplication(UniversityApplication application) async {
    final apps = await getApplications();
    apps.add(application);
    await _saveUniversityApps(apps);
  }

  @override
  Future<void> updateApplication(UniversityApplication application) async {
    final apps = await getApplications();
    final index = apps.indexWhere((a) => a.id == application.id);
    if (index != -1) {
      apps[index] = application;
      await _saveUniversityApps(apps);
    }
  }

  @override
  Future<void> deleteApplication(String id) async {
    final apps = await getApplications();
    apps.removeWhere((a) => a.id == id);
    await _saveUniversityApps(apps);
  }

  Future<void> _saveUniversityApps(List<UniversityApplication> apps) async {
    final json = jsonEncode(apps.map((a) => a.toJson()).toList());
    await HiveDatabase.applications.put('university_apps', json);
  }

  @override
  Stream<List<UniversityApplication>> watchApplications() {
    return HiveDatabase.applications.watch().map((_) {
      final raw = HiveDatabase.applications.get('university_apps');
      if (raw == null || raw.isEmpty) return [];
      try {
        final list = jsonDecode(raw) as List;
        return list.map((e) => UniversityApplication.fromJson(e)).toList();
      } catch (_) {
        return [];
      }
    });
  }

  @override
  Future<List<BursaryApplication>> getBursaryApplications() async {
    final raw = HiveDatabase.applications.get('bursary_apps');
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List;
      return list.map((e) => BursaryApplication.fromJson(e)).toList();
    } catch (_) {
      return [];
    }
  }

  @override
  Future<void> saveBursaryApplication(BursaryApplication application) async {
    final apps = await getBursaryApplications();
    apps.add(application);
    await _saveBursaryApps(apps);
  }

  @override
  Future<void> updateBursaryApplication(BursaryApplication application) async {
    final apps = await getBursaryApplications();
    final index = apps.indexWhere((a) => a.id == application.id);
    if (index != -1) {
      apps[index] = application;
      await _saveBursaryApps(apps);
    }
  }

  @override
  Future<void> deleteBursaryApplication(String id) async {
    final apps = await getBursaryApplications();
    apps.removeWhere((a) => a.id == id);
    await _saveBursaryApps(apps);
  }

  Future<void> _saveBursaryApps(List<BursaryApplication> apps) async {
    final json = jsonEncode(apps.map((a) => a.toJson()).toList());
    await HiveDatabase.applications.put('bursary_apps', json);
  }
}
