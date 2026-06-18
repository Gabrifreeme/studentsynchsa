import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsynchsa/data/repositories/application_repository_impl.dart';
import 'package:studentsynchsa/domain/models/application.dart';
import 'package:studentsynchsa/domain/models/bursary.dart';
import 'package:studentsynchsa/domain/repositories/application_repository.dart';

class ApplicationsNotifier extends StateNotifier<AsyncValue<List<UniversityApplication>>> {
  late final ApplicationRepository _repo;

  ApplicationsNotifier() : super(const AsyncLoading()) {
    _repo = ApplicationRepositoryImpl();
    _init();
  }

  Future<void> _init() async {
    try {
      final apps = await _repo.getApplications();
      state = AsyncData(apps);
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
    }
  }

  Future<void> save(UniversityApplication app) async {
    await _repo.saveApplication(app);
    final apps = await _repo.getApplications();
    state = AsyncData(apps);
  }

  Future<void> update(UniversityApplication app) async {
    await _repo.updateApplication(app);
    final apps = await _repo.getApplications();
    state = AsyncData(apps);
  }

  Future<void> delete(String id) async {
    await _repo.deleteApplication(id);
    final apps = await _repo.getApplications();
    state = AsyncData(apps);
  }
}

class BursaryApplicationsNotifier extends StateNotifier<AsyncValue<List<BursaryApplication>>> {
  late final ApplicationRepository _repo;

  BursaryApplicationsNotifier() : super(const AsyncLoading()) {
    _repo = ApplicationRepositoryImpl();
    _init();
  }

  Future<void> _init() async {
    try {
      final apps = await _repo.getBursaryApplications();
      state = AsyncData(apps);
    } catch (e) {
      state = AsyncError(e, StackTrace.current);
    }
  }

  Future<void> save(BursaryApplication app) async {
    await _repo.saveBursaryApplication(app);
    final apps = await _repo.getBursaryApplications();
    state = AsyncData(apps);
  }

  Future<void> update(BursaryApplication app) async {
    await _repo.updateBursaryApplication(app);
    final apps = await _repo.getBursaryApplications();
    state = AsyncData(apps);
  }

  Future<void> delete(String id) async {
    await _repo.deleteBursaryApplication(id);
    final apps = await _repo.getBursaryApplications();
    state = AsyncData(apps);
  }
}

final applicationsProvider = StateNotifierProvider<ApplicationsNotifier, AsyncValue<List<UniversityApplication>>>((ref) {
  return ApplicationsNotifier();
});

final bursaryApplicationsProvider = StateNotifierProvider<BursaryApplicationsNotifier, AsyncValue<List<BursaryApplication>>>((ref) {
  return BursaryApplicationsNotifier();
});
