import 'package:flutter/services.dart';

class AccessibilityBridge {
  static const _channel = MethodChannel('studentsyncsa/accessibility');

  Future<bool> isServiceEnabled() async {
    try {
      return await _channel.invokeMethod('isServiceEnabled') ?? false;
    } catch (_) {
      return false;
    }
  }

  Future<void> openSettings() async {
    try {
      await _channel.invokeMethod('openAccessibilitySettings');
    } catch (_) {}
  }

  Future<List<Map<String, String>>> scan() async {
    try {
      final raw = await _channel.invokeMethod('scan');
      if (raw is List) {
        return raw.cast<Map<String, String>>();
      }
    } catch (_) {}
    return [];
  }

  Future<bool> fillFocused(String text) async {
    try {
      return await _channel.invokeMethod('fillFocused', {'text': text}) ?? false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> fillField(String keyword, String value) async {
    try {
      return await _channel.invokeMethod('fillField', {
        'keyword': keyword,
        'value': value,
      }) ?? false;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, bool>> fillAll(List<Map<String, String>> fields) async {
    try {
      final raw = await _channel.invokeMethod('fillAll', {'fields': fields});
      if (raw is Map) {
        return raw.map((k, v) => MapEntry(k.toString(), v == true));
      }
    } catch (_) {}
    return {};
  }
}
