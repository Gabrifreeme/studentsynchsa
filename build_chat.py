import io, os

# ============================================================
# 1. Message Model
# ============================================================
model_code = """import 'dart:convert';

class ChatMessage {
  final String id;
  final String room;      // 'general' | 'province' | 'university'
  final String sender;    // 'You' or a name
  final String text;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.room,
    required this.sender,
    required this.text,
    required this.timestamp,
  });

  Map<String, dynamic> toMap() => {
        'id': id,
        'room': room,
        'sender': sender,
        'text': text,
        'timestamp': timestamp.toIso8601String(),
      };

  factory ChatMessage.fromMap(Map<String, dynamic> map) => ChatMessage(
        id: map['id'] as String,
        room: map['room'] as String,
        sender: map['sender'] as String,
        text: map['text'] as String,
        timestamp: DateTime.parse(map['timestamp'] as String),
      );

  String toJson() => jsonEncode(toMap());

  factory ChatMessage.fromJson(String json) =>
      ChatMessage.fromMap(jsonDecode(json) as Map<String, dynamic>);
}
"""

# ============================================================
# 2. Chat Storage
# ============================================================
storage_code = """import 'package:hive_flutter/hive_flutter.dart';
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
"""

# ============================================================
# 3. Room Chat Screen
# ============================================================
screen_code = """import 'package:flutter/material.dart';
import 'package:lipsyncstudent/core/theme/app_theme.dart';
import 'package:lipsyncstudent/data/datasources/local/chat_storage.dart';
import 'package:lipsyncstudent/data/models/chat_message.dart';
import 'package:uuid/uuid.dart';

class RoomChatScreen extends StatefulWidget {
  final String room;      // 'general' | 'province' | 'university'
  final String roomName;  // 'General Chat', etc.
  const RoomChatScreen({super.key, required this.room, required this.roomName});

  @override
  State<RoomChatScreen> createState() => _RoomChatScreenState();
}

class _RoomChatScreenState extends State<RoomChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scroll = ScrollController();
  List<ChatMessage> _messages = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final messages = await ChatStorage.getMessages(widget.room);
    if (!mounted) return;
    setState(() {
      _messages = messages;
      _loading = false;
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    final message = ChatMessage(
      id: const Uuid().v4(),
      room: widget.room,
      sender: 'You',
      text: text,
      timestamp: DateTime.now(),
    );
    await ChatStorage.addMessage(message);
    _controller.clear();
    if (!mounted) return;
    setState(() => _messages = [..._messages, message]);
    _scrollToBottom();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black,
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          title: Text(widget.roomName),
          centerTitle: true,
          backgroundColor: Colors.black,
          elevation: 0,
        ),
        body: _loading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.primary))
            : Column(
                children: [
                  Expanded(
                    child: _messages.isEmpty
                        ? const Center(
                            child: Text(
                              'No messages yet. Say hi!',
                              style: TextStyle(color: AppColors.textMuted),
                            ),
                          )
                        : ListView.builder(
                            controller: _scroll,
                            padding: const EdgeInsets.all(12),
                            itemCount: _messages.length,
                            itemBuilder: (ctx, i) {
                              final m = _messages[i];
                              final isMe = m.sender == 'You';
                              return Align(
                                alignment: isMe
                                    ? Alignment.centerRight
                                    : Alignment.centerLeft,
                                child: Container(
                                  margin: const EdgeInsets.symmetric(vertical: 4),
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 12, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: isMe
                                        ? AppColors.primary.withValues(alpha: 0.2)
                                        : AppColors.surface,
                                    border: Border.all(
                                        color: AppColors.primary, width: 1),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        m.sender,
                                        style: const TextStyle(
                                          color: AppColors.primary,
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        m.text,
                                        style: const TextStyle(
                                          color: AppColors.primary,
                                          fontSize: 14,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                  ),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: const BoxDecoration(
                      color: Colors.black,
                      border: Border(
                          top: BorderSide(color: AppColors.primary, width: 1)),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _controller,
                            style: const TextStyle(
                                color: AppColors.primary, fontSize: 14),
                            decoration: const InputDecoration(
                              hintText: 'Type a message...',
                              hintStyle: TextStyle(color: AppColors.textMuted),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.zero,
                                borderSide:
                                    BorderSide(color: AppColors.primary),
                              ),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.zero,
                                borderSide:
                                    BorderSide(color: AppColors.primary),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.zero,
                                borderSide: BorderSide(
                                    color: AppColors.primary, width: 2),
                              ),
                              contentPadding: EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                            ),
                            onSubmitted: (_) => _send(),
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          onPressed: _send,
                          icon: const Icon(Icons.send,
                              color: AppColors.primary),
                          style: IconButton.styleFrom(
                            backgroundColor: AppColors.surface,
                            shape: const RoundedRectangleBorder(
                              borderRadius: BorderRadius.zero,
                              side: BorderSide(color: AppColors.primary),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
"""

# Write new files
files = {
    r"C:\Users\chris\LipSyncStudent\lib\data\models\chat_message.dart": model_code,
    r"C:\Users\chris\LipSyncStudent\lib\data\datasources\local\chat_storage.dart": storage_code,
    r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart": screen_code,
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)
    print(f"CREATED: {path.split(chr(92))[-1]}")

# ============================================================
# 4. Patch chat_screen.dart to navigate to RoomChatScreen
# ============================================================
chat_screen_path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\chat_screen.dart"
with io.open(chat_screen_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# Add import
if "room_chat_screen.dart" not in content:
    content = content.replace(
        "import 'package:lipsyncstudent/core/theme/app_theme.dart';",
        "import 'package:lipsyncstudent/core/theme/app_theme.dart';\r\nimport 'package:lipsyncstudent/presentation/screens/chat/room_chat_screen.dart';",
        1
    )
    print("PATCHED: added room_chat_screen import")

# Replace _showComingSoon calls with navigation
old_general = "onTap: () => _showComingSoon(context),\r\n              child: const ListTile(\r\n                leading: Icon(Icons.chat_rounded, color: AppColors.primary),"
new_general = "onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomChatScreen(room: 'general', roomName: 'General Chat'))),\r\n              child: const ListTile(\r\n                leading: Icon(Icons.chat_rounded, color: AppColors.primary),"

old_province = "onTap: () => _showComingSoon(context),\r\n              child: const ListTile(\r\n                leading:\r\n                    Icon(Icons.map_rounded, color: AppColors.success),"
new_province = "onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomChatScreen(room: 'province', roomName: 'Province-based'))),\r\n              child: const ListTile(\r\n                leading:\r\n                    Icon(Icons.map_rounded, color: AppColors.success),"

old_university = "onTap: () => _showComingSoon(context),\r\n              child: const ListTile(\r\n                leading:\r\n                    Icon(Icons.school_rounded, color: AppColors.warning),"
new_university = "onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomChatScreen(room: 'university', roomName: 'University Interest Groups'))),\r\n              child: const ListTile(\r\n                leading:\r\n                    Icon(Icons.school_rounded, color: AppColors.warning),"

replaced = 0
for old, new, name in [(old_general, new_general, 'general'),
                       (old_province, new_province, 'province'),
                       (old_university, new_university, 'university')]:
    if old in content:
        content = content.replace(old, new)
        replaced += 1
        print(f"PATCHED: {name} card -> RoomChatScreen")

if replaced == 0:
    print("WARNING: No card replacements fired - check line endings")

with io.open(chat_screen_path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE")
