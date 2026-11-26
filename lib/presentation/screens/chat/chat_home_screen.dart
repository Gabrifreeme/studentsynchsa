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
      padding: const EdgeInsets.fromLTRB(8, 6, 8, 0),
      child: AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        onTap: () => setState(() => _selected = i),
        child: ListTile(
          dense: true,
          visualDensity: VisualDensity.compact,
          leading: Stack(
            clipBehavior: Clip.none,
            children: [
              StarIcon(room.$3, size: 20),
              if (unread > 0)
                Positioned(
                  right: -6,
                  top: -6,
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
          title: Text(room.$1,
              style: TextStyle(
                  color: active ? AppColors.primary : AppColors.textPrimary,
                  fontSize: 12,
                  fontWeight: FontWeight.w600)),
          subtitle: Text(room.$4,
              style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 9)),
          trailing: Icon(Icons.chevron_right_rounded,
              color: active ? AppColors.primary : AppColors.textMuted,
              size: 16),
        ),
      ),
    );
  }
}
