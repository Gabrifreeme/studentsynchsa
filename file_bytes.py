import io

# ============ 1. Update ChatMessage model ============
model_path = r"C:\Users\chris\LipSyncStudent\lib\data\models\chat_message.dart"
model_code = """import 'dart:convert';

class ChatMessage {
  final String id;
  final String room;
  final String sender;
  final String text;
  final DateTime timestamp;
  final String? fileData;    // base64-encoded file bytes
  final String? mimeType;    // e.g., 'image/png'

  ChatMessage({
    required this.id,
    required this.room,
    required this.sender,
    required this.text,
    required this.timestamp,
    this.fileData,
    this.mimeType,
  });

  Map<String, dynamic> toMap() => {
        'id': id,
        'room': room,
        'sender': sender,
        'text': text,
        'timestamp': timestamp.toIso8601String(),
        if (fileData != null) 'fileData': fileData,
        if (mimeType != null) 'mimeType': mimeType,
      };

  factory ChatMessage.fromMap(Map<String, dynamic> map) => ChatMessage(
        id: map['id'] as String,
        room: map['room'] as String,
        sender: map['sender'] as String,
        text: map['text'] as String,
        timestamp: DateTime.parse(map['timestamp'] as String),
        fileData: map['fileData'] as String?,
        mimeType: map['mimeType'] as String?,
      );

  String toJson() => jsonEncode(toMap());

  factory ChatMessage.fromJson(String json) =>
      ChatMessage.fromMap(jsonDecode(json) as Map<String, dynamic>);
}
"""
with io.open(model_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(model_code)
print("UPDATED: ChatMessage model with fileData + mimeType")

# ============ 2. Update room_chat_screen.dart ============
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# 2a. Add dart:convert import
if "import 'dart:convert';" not in content:
    content = content.replace(
        "import 'dart:async';",
        "import 'dart:async';\r\nimport 'dart:convert';",
        1
    )
    print("ADDED: dart:convert import")

# 2b. Update _pickFile to read bytes
old_pick = """      final result = await FilePicker.pickFiles();
      if (result.isEmpty) return;
      final file = result.first;
      final fileName = file.name;
      final filePath = file.path ?? '';
      final tag = filePath.isNotEmpty ? '[FILE] $fileName' : '[FILE] $fileName';
      await _sendMessage(tag);"""

new_pick = """      final result = await FilePicker.pickFiles(withData: true);
      if (result.isEmpty) return;
      final file = result.first;
      final fileName = file.name;
      final bytes = file.bytes;
      String? base64Data;
      String? mimeType;
      if (bytes != null) {
        base64Data = base64Encode(bytes);
        final ext = fileName.split('.').last.toLowerCase();
        mimeType = ext == 'png' ? 'image/png'
            : ext == 'jpg' || ext == 'jpeg' ? 'image/jpeg'
            : ext == 'pdf' ? 'application/pdf'
            : ext == 'txt' ? 'text/plain'
            : 'application/octet-stream';
      }
      // Send message with file data
      final message = ChatMessage(
        id: const Uuid().v4(),
        room: widget.room,
        sender: 'You',
        text: '[FILE] ' + fileName,
        timestamp: DateTime.now(),
        fileData: base64Data,
        mimeType: mimeType,
      );
      await ChatStorage.addMessage(message);
      _controller.clear();
      if (!mounted) return;
      setState(() => _messages = [..._messages, message]);
      _scrollToBottom();"""

if old_pick in content:
    content = content.replace(old_pick, new_pick)
    print("PATCHED: _pickFile reads bytes and stores base64")
else:
    print("WARNING: _pickFile pattern not found")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE")
