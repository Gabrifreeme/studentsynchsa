import 'dart:convert';

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
