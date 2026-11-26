import 'dart:async';

import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/chat/general_chat_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// Chat home: a vertical list of three room buttons with unread badges.
/// Tapping one opens that conversation immediately — no slide-out menu.
class ChatHomeScreen extends StatefulWidget {
  const ChatHomeScreen({super.key});

  @override
  State<ChatHomeScreen> createState() => _ChatHomeScreenState();
}

class _ChatHomeScreenState extends State<ChatHomeScreen> {
  int _selected = 0; // General Chat by default
  final Map<String, int> _unread = {};
  Timer? _poll;

  static const _rooms = [
    ('General Chat', 'general', Icons.forum_rounded, 'Talk to all students'),
    ('Province Base Chat', 'province', Icons.map_rounded,
        'Students in your province'),
    ('University Chat', 'university', Icons.school_rounded,
        'Future classmates'),
  ];

  @override
  void initState() {
    super.initState();
    if (ChatService.isConfigured) {
      _checkUnread();
      _poll = Timer.periodic(const Duration(seconds: 5), (_) => _checkUnread());
    }
  }

  @override
  void dispose() {
    _poll?.cancel();
    super.dispose();
  }

  Future<void> _checkUnread() async {
    for (final room in _rooms) {
      try {
        final rows = await ChatService.fetchMessages(room.$2);
        final read = ChatService.readCount(room.$2);
        if (!mounted) return;
        setState(() =>
            _unread[room.$2] = rows.length > read ? rows.length - read : 0);
      } catch (_) {}
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Community Chat')),
      body: Column(
        children: [
          ...List.generate(_rooms.length, (i) => _roomCard(i)),
          Expanded(
            child: GeneralChatScreen(
              room: _rooms[_selected].$2,
              title: _rooms[_selected].$1,
            ),
          ),
        ],
      ),
    );
  }

  Widget _roomCard(int i) {
    final room = _rooms[i];
    final active = _selected == i;
    final unread = _unread[room.$2] ?? 0;
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 5, 0, 0),
      child: GestureDetector(
        onTap: () => setState(() => _selected = i),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              width: 40,
              height: 40,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: active
                    ? AppColors.primary.withValues(alpha: 0.16)
                    : AppColors.surfaceLight,
                border: Border.all(
                    color: active ? AppColors.primary : AppColors.border,
                    width: 1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: StarIcon(room.$3, size: 21),
            ),
            if (unread > 0)
              Positioned(
                right: -5,
                top: -5,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                  decoration: const BoxDecoration(
                      color: Color(0xFFFF4444), shape: BoxShape.circle),
                  child: Text('$unread',
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 8,
                          fontWeight: FontWeight.w700)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
