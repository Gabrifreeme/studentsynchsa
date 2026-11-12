import 'package:hive_flutter/hive_flutter.dart';
import 'package:lipsyncstudent/data/models/chat_message.dart';

class ChatStorage {
  static const String boxName = 'chat_messages';

  static Future<Box<String>> _box() async {
    if (Hive.isBoxOpen(boxName)) return Hive.box<String>(boxName);
    return await Hive.openBox<String>(boxName);
  }

  static Future<void> addMessage(ChatMessage message) async {
    final box = await _box();
    await box.put(message.id, message.toJson());
  }

  static Future<List<ChatMessage>> getMessages(String room) async {
    final box = await _box();
    final messages = <ChatMessage>[];
    for (final key in box.keys) {
      final raw = box.get(key);
      if (raw == null) continue;
      try {
        final msg = ChatMessage.fromJson(raw);
        if (msg.room == room) messages.add(msg);
      } catch (_) {}
    }
    messages.sort((a, b) => a.timestamp.compareTo(b.timestamp));
    return messages;
  }

  static Future<void> clearRoom(String room) async {
    final box = await _box();
    final toDelete = <dynamic>[];
    for (final key in box.keys) {
      final raw = box.get(key);
      if (raw == null) continue;
      try {
        if (ChatMessage.fromJson(raw).room == room) toDelete.add(key);
      } catch (_) {}
    }
    await box.deleteAll(toDelete);
  }
}
