import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lipsyncstudent/services/sync_service.dart' as sync_service;

class SyncStatusNotifier extends StateNotifier<AsyncValue<sync_service.SyncStatus>> {
  StreamSubscription<sync_service.SyncStatus>? _sub;

  SyncStatusNotifier() : super(const AsyncLoading()) {
    _sub = sync_service.SyncService.statusStream.listen((status) {
      state = AsyncData<sync_service.SyncStatus>(status);
    });
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}

final syncStatusNotifierProvider = StateNotifierProvider<SyncStatusNotifier, AsyncValue<sync_service.SyncStatus>>((ref) {
  return SyncStatusNotifier();
});