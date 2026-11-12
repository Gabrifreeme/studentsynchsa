// chat_service.dart
// Phase 2a: cross-device chat over socket_io_client 3.x, namespace /chat.
// Server is authoritative: send() does NOT optimistically render. The server
// echoes chat_message, which we persist via ChatStorage and emit on the stream.
// The UI reads from ChatStorage (single source of truth); the stream signals
// "the box changed, reload".
//
// Token: optional. Stored in Hive _meta box under 'chat_token'. Absent token +
// loopback = Guest. Non-loopback without token = 401 on chat_connect.
//
// Attachments (fileData / mimeType) are local-only in 2a. send() rejects
// attachmentJson. The UI surfaces this rather than silently producing
// unsynced messages.

import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:socket_io_client/socket_io_client.dart' as io;

import 'package:lipsyncstudent/data/datasources/local/chat_storage.dart';
import 'package:lipsyncstudent/data/models/chat_message.dart';

enum ChatConnectionState { disconnected, connecting, connected, reconnecting, error }

class ChatEvent {
  final ChatConnectionState state;
  final String? message;
  ChatEvent(this.state, [this.message]);
  @override
  String toString() => 'ChatEvent($state${message != null ? ": $message" : ""})';
}

class ChatService {
  ChatService._();
  static final ChatService instance = ChatService._();

  static const String _metaBoxName = '_meta';
  static const String _tokenKey = 'chat_token';
  static const String _serverBaseUrl = String.fromEnvironment(
    'ACE_CHAT_URL',
    defaultValue: 'http://127.0.0.1:5000',
  );

  io.Socket? _socket;
  String? _currentRoom;
  String? _currentToken;
  bool _connecting = false;

  final StreamController<ChatMessage> _msgCtrl =
      StreamController<ChatMessage>.broadcast();
  final StreamController<ChatEvent> _statusCtrl =
      StreamController<ChatEvent>.broadcast();

  Stream<ChatMessage> get messages => _msgCtrl.stream;
  Stream<ChatEvent> get status => _statusCtrl.stream;

  bool get isConnected => _socket?.connected ?? false;
  String? get currentRoom => _currentRoom;

  String? _currentDisplayName;
  String? get currentDisplayName => _currentDisplayName;

  ChatConnectionState _lastState = ChatConnectionState.disconnected;
  ChatConnectionState get lastState => _lastState;

  Future<String?> _readToken() async {
    try {
      final box = Hive.isBoxOpen(_metaBoxName)
          ? Hive.box<dynamic>(_metaBoxName)
          : await Hive.openBox<dynamic>(_metaBoxName);
      final v = box.get(_tokenKey);
      if (v is String && v.isNotEmpty) return v;
      return null;
    } catch (_) {
      return null;
    }
  }

  Future<void> setToken(String? token) async {
    final box = Hive.isBoxOpen(_metaBoxName)
        ? Hive.box<dynamic>(_metaBoxName)
        : await Hive.openBox<dynamic>(_metaBoxName);
    if (token == null || token.isEmpty) {
      await box.delete(_tokenKey);
    } else {
      await box.put(_tokenKey, token);
    }
  }

  void _emitStatus(ChatConnectionState s, [String? message]) {
    _lastState = s;
    if (!_statusCtrl.isClosed) _statusCtrl.add(ChatEvent(s, message));
  }

  Future<void> connect(String room) async {
    if (_connecting) return;
    if (_socket != null && _currentRoom == room) return;
    _connecting = true;
    try {
      _currentToken = await _readToken();
      _currentRoom = room;

      _socket?.dispose();
      _socket = null;

      _emitStatus(ChatConnectionState.connecting);

      final socket = io.io(
        _serverBaseUrl,
        io.OptionBuilder()
            .setTransports(['websocket'])
            .disableAutoConnect()
            .setPath('/socket.io')
            .build(),
      );

      socket.onConnect((_) {
        _emitStatus(ChatConnectionState.connected);
        final payload = <String, dynamic>{'room_id': room};
        if (_currentToken != null) payload['token'] = _currentToken;
        socket.emit('chat_connect', payload);
      });

      socket.on('chat_joined', (data) async {
        try {
          final map = (data as Map).cast<String, dynamic>();
          final dn = map['display_name'];
          if (dn is String) _currentDisplayName = dn;
          final recent = (map['recent'] as List?) ?? const [];
          for (final raw in recent) {
            final m = _fromServerJson((raw as Map).cast<String, dynamic>());
            await ChatStorage.addMessage(m);
            if (!_msgCtrl.isClosed) _msgCtrl.add(m);
          }
          _emitStatus(ChatConnectionState.connected);
        } catch (e) {
          _emitStatus(ChatConnectionState.error, 'chat_joined parse: $e');
        }
      });

      socket.on('chat_message', (data) async {
        try {
          final m = _fromServerJson((data as Map).cast<String, dynamic>());
          await ChatStorage.addMessage(m);
          if (!_msgCtrl.isClosed) _msgCtrl.add(m);
        } catch (e) {
          _emitStatus(ChatConnectionState.error, 'chat_message parse: $e');
        }
      });

      socket.on('chat_error', (data) {
        final msg = (data is Map ? data['error'] : data)?.toString() ?? 'unknown';
        _emitStatus(ChatConnectionState.error, msg);
      });

      socket.onDisconnect((_) {
        if (_lastState != ChatConnectionState.error) {
          _emitStatus(ChatConnectionState.disconnected);
        }
      });

      socket.onConnectError((err) {
        _emitStatus(ChatConnectionState.error, err?.toString());
      });

      socket.onReconnectAttempt((_) {
        _emitStatus(ChatConnectionState.reconnecting);
      });

      socket.onReconnect((_) {
        _emitStatus(ChatConnectionState.connected);
        final payload = <String, dynamic>{'room_id': room};
        if (_currentToken != null) payload['token'] = _currentToken;
        socket.emit('chat_connect', payload);
      });

      socket.connect();
      _socket = socket;
    } finally {
      _connecting = false;
    }
  }

  Future<void> send({
    required String room,
    required String body,
    String? attachmentJson,
  }) async {
    if (_socket == null || !_socket!.connected) {
      throw StateError('ChatService not connected');
    }
    if (_currentRoom != room) {
      throw StateError('ChatService connected to $_currentRoom, not $room');
    }
    if (attachmentJson != null) {
      throw UnsupportedError(
        'Attachments do not sync in this build; they are stored locally only.',
      );
    }
    if (body.trim().isEmpty) {
      throw ArgumentError('body is empty');
    }
    _socket!.emit('chat_send', <String, dynamic>{'body': body});
  }

  void disconnect() {
    _socket?.dispose();
    _socket = null;
    _currentRoom = null;
    _emitStatus(ChatConnectionState.disconnected);
  }

  ChatMessage _fromServerJson(Map<String, dynamic> j) {
    final int sid = (j['id'] as num).toInt();
    final attachment = j['attachment_json'] as String?;
    String? fileData;
    String? mimeType;
    if (attachment != null && attachment.isNotEmpty) {
      try {
        final a = jsonDecode(attachment) as Map<String, dynamic>;
        fileData = a['data'] as String?;
        mimeType = a['mime'] as String?;
      } catch (_) {}
    }
    return ChatMessage(
      id: 'srv:$sid',
      room: j['room_id'] as String,
      sender: (j['display_name'] ?? 'Unknown') as String,
      text: (j['body'] ?? '') as String,
      timestamp: DateTime.parse(j['created_at'] as String),
      fileData: fileData,
      mimeType: mimeType,
    );
  }

  @visibleForTesting
  void debugEmitStatus(ChatConnectionState s, [String? m]) => _emitStatus(s, m);
}
