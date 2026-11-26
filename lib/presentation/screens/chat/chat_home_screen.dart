import 'dart:async';

import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/chat/general_chat_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// Community opens with a left slide-out panel showing room icons and the
/// chat/contact list. Selecting a room closes the panel and opens that chat.
class ChatHomeScreen extends StatefulWidget {
  const ChatHomeScreen({super.key});

  @override
  State<ChatHomeScreen> createState() => _ChatHomeScreenState();
}

class _ChatHomeScreenState extends State<ChatHomeScreen> {
  int _selected = 0; // General Chat is the open conversation
  bool _panelOpen = false;
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
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) setState(() => _panelOpen = true);
    });
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
    final w = MediaQuery.of(context).size.width;
    final panelWidth = w < 600 ? w * 0.82 : 300.0;
    return Stack(
      children: [
        GeneralChatScreen(
          room: _rooms[_selected].$2,
          title: _rooms[_selected].$1,
          topStrip: _topStrip(),
          onBack: () => setState(() => _panelOpen = true),
        ),
        // Scrim closes the panel.
        if (_panelOpen)
          Positioned.fill(
            child: GestureDetector(
              onTap: () => setState(() => _panelOpen = false),
              child: Container(color: Colors.black54),
            ),
          ),
        AnimatedPositioned(
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOut,
          left: _panelOpen ? 0 : -panelWidth,
          top: 0,
          bottom: 0,
          width: panelWidth,
          child: _panel(),
        ),
      ],
    );
  }

  /// Icons + a button to reopen the panel, shown under the chat title.
  Widget _topStrip() => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              tooltip: 'Open chats',
              icon: const StarIcon(Icons.menu_rounded, size: 19),
              onPressed: () => setState(() => _panelOpen = true),
            ),
            ...List.generate(_rooms.length, (i) => _icon(i)),
          ],
        ),
      );

  Widget _icon(int i) {
    final room = _rooms[i];
    final active = _selected == i;
    final unread = _unread[room.$2] ?? 0;
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: GestureDetector(
        onTap: () {
          setState(() {
            _selected = i;
            _panelOpen = false;
          });
        },
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              width: 36,
              height: 36,
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
              child: StarIcon(room.$3, size: 20),
            ),
            if (unread > 0)
              Positioned(
                right: -5,
                top: -5,
                child: _badge(unread),
              ),
          ],
        ),
      ),
    );
  }

  Widget _badge(int n) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
        decoration: const BoxDecoration(
            color: Color(0xFFFF4444), shape: BoxShape.circle),
        child: Text('$n',
            style: const TextStyle(
                color: Colors.white, fontSize: 8, fontWeight: FontWeight.w700)),
      );

  Widget _panel() => Container(
        decoration: const BoxDecoration(
          color: Color(0xFF080808),
          border: Border(right: BorderSide(color: AppColors.border, width: 1)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 16, 12, 10),
              child: Row(
                children: [
                  const Text('CHATS',
                      style: TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 10,
                          letterSpacing: 1.5)),
                  const Spacer(),
                  IconButton(
                    icon: const StarIcon(Icons.close_rounded, size: 18),
                    onPressed: () => setState(() => _panelOpen = false),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children:
                    List.generate(_rooms.length, (i) => _icon(i)),
              ),
            ),
            const SizedBox(height: 10),
            const Expanded(child: SizedBox.shrink()),
          ],
        ),
      );


}
