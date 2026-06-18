import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:studentsynchsa/core/constants/app_constants.dart';
import 'package:studentsynchsa/data/datasources/local/hive_database.dart';
import 'package:studentsynchsa/domain/models/student_profile.dart';

enum SyncStatus { offline, syncing, synced, failed }

class SyncService {
  static final Connectivity _connectivity = Connectivity();
  static final _statusController = StreamController<SyncStatus>.broadcast();
  static StreamSubscription? _connectivitySub;
  static Timer? _syncTimer;
  static SyncStatus _currentStatus = SyncStatus.offline;

  static Stream<SyncStatus> get statusStream => _statusController.stream;
  static SyncStatus get currentStatus => _currentStatus;

  static Future<void> init() async {
    _connectivitySub = _connectivity.onConnectivityChanged.listen((results) {
      final hasConnection = results.any(
        (r) => r != ConnectivityResult.none,
      );
      if (hasConnection && _currentStatus == SyncStatus.offline) {
        _setStatus(SyncStatus.synced);
        _syncProfile();
      } else if (!hasConnection) {
        _setStatus(SyncStatus.offline);
      }
    });
    _syncTimer = Timer.periodic(AppConstants.syncInterval, (_) {
      if (_currentStatus != SyncStatus.offline) {
        _syncProfile();
      }
    });
  }

  static void _setStatus(SyncStatus status) {
    _currentStatus = status;
    _statusController.add(status);
  }

  static Future<void> _syncProfile() async {
    _setStatus(SyncStatus.syncing);
    try {
      final raw = HiveDatabase.profile.get('profile');
      if (raw == null || raw.isEmpty) {
        _setStatus(SyncStatus.synced);
        return;
      }
      final client = HttpClient();
      client.connectionTimeout = const Duration(seconds: 5);
      final request = await client.postUrl(
        Uri.parse('${AppConstants.serverUrl}/api/save-profile'),
      );
      request.headers.contentType = ContentType.json;
      request.write(raw);
      final response = await request.close();
      if (response.statusCode == 200) {
        await HiveDatabase.settings.put(
          'last_sync',
          DateTime.now().toIso8601String(),
        );
        _setStatus(SyncStatus.synced);
      } else {
        _setStatus(SyncStatus.failed);
      }
    } catch (_) {
      _setStatus(SyncStatus.failed);
    }
  }

  static Future<void> triggerSync() async {
    if (_currentStatus != SyncStatus.offline) {
      await _syncProfile();
    }
  }

  static Future<StudentProfile?> tryServerRestore() async {
    try {
      final client = HttpClient();
      client.connectionTimeout = const Duration(seconds: 5);
      final request = await client.getUrl(
        Uri.parse('${AppConstants.serverUrl}/api/profile'),
      );
      final response = await request.close();
      if (response.statusCode == 200) {
        final body = await response.transform(utf8.decoder).join();
        final data = jsonDecode(body);
        if (data != null && data is Map<String, dynamic>) {
          return StudentProfile.fromJson(data);
        }
      }
    } catch (_) {}
    return null;
  }

  static Future<DateTime?> getLastSyncTime() async {
    final raw = HiveDatabase.settings.get('last_sync');
    if (raw == null) return null;
    return DateTime.tryParse(raw);
  }

  static void dispose() {
    _connectivitySub?.cancel();
    _syncTimer?.cancel();
    _statusController.close();
  }
}
