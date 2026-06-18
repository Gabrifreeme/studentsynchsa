import 'package:hive_flutter/hive_flutter.dart';
import 'package:studentsynchsa/core/constants/app_constants.dart';

class HiveDatabase {
  static late Box<String> _profileBox;
  static late Box<String> _applicationsBox;
  static late Box<String> _universitiesBox;
  static late Box<String> _bursariesBox;
  static late Box<String> _notificationsBox;
  static late Box<String> _settingsBox;

  static Future<void> init() async {
    await Hive.initFlutter();
    _profileBox = await Hive.openBox<String>(AppConstants.profileBox);
    _applicationsBox = await Hive.openBox<String>(AppConstants.applicationsBox);
    _universitiesBox = await Hive.openBox<String>(AppConstants.universitiesBox);
    _bursariesBox = await Hive.openBox<String>(AppConstants.bursariesBox);
    _notificationsBox = await Hive.openBox<String>(AppConstants.notificationsBox);
    _settingsBox = await Hive.openBox<String>(AppConstants.settingsBox);
  }

  // Profile
  static Box<String> get profile => _profileBox;
  static Box<String> get applications => _applicationsBox;
  static Box<String> get universities => _universitiesBox;
  static Box<String> get bursaries => _bursariesBox;
  static Box<String> get notifications => _notificationsBox;
  static Box<String> get settings => _settingsBox;

  static Future<void> clearAll() async {
    await _profileBox.clear();
    await _applicationsBox.clear();
    await _universitiesBox.clear();
    await _bursariesBox.clear();
    await _notificationsBox.clear();
  }
}
