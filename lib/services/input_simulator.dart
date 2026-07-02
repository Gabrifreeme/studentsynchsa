import 'package:flutter/services.dart';

class InputSimulator {
  static const _channel = MethodChannel('studentsyncsa/input');

  Future<bool> type(String text) async {
    try {
      return await _channel.invokeMethod('type', {'text': text}) ?? false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> tab() async {
    try {
      return await _channel.invokeMethod('tab') ?? false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> enter() async {
    try {
      return await _channel.invokeMethod('enter') ?? false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> clear() async {
    try {
      return await _channel.invokeMethod('clear') ?? false;
    } catch (_) {
      return false;
    }
  }
}
