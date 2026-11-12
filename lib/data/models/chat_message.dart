import 'dart:convert';

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
