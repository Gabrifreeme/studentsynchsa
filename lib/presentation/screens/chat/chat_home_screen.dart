import 'dart:async';

import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/chat/general_chat_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// Opens straight into General Chat. A compact strip of room icons with
/// unread badges sits at the top; the full room panel is opt-in via a button.
class ChatHomeScreen extends StatefulWidget {
  const ChatHomeScreen({super.key});

  @override
  State<ChatHomeScreen> createState() => _ChatHomeScreenState();
}

class _ChatHomeScreenState extends State<ChatHomeScreen> {
  int _selected = 0; // General Chat by default
  bool _menuOpen = false;
  final Map<String, int> _unread = {};
  Timer? _poll;

  static const _rooms = [
    ('General Chat', 'general', Icons.forum_rounded),
    ('Province-based', 'province', Icons.map_rounded),
    ('University', 'university', Icons.school_rounded),
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
    final wide = MediaQuery.of(context).size.width >= 700;
    return Scaffold(
      appBar: AppBar(title: const Text('Community Chat')),
      body: Column(
        children: [
          _roomStrip(),
          if (wide && _menuOpen)
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(width: 230, child: _list()),
                  const VerticalDivider(width: 1, color: AppColors.border),
                  Expanded(child: _pane()),
                ],
              ),
            )
          else
            Expanded(child: _pane()),
        ],
      ),
    );
  }

  /// Compact row of room icons with red unread badges + the panel button.
  Widget _roomStrip() => Container(
        decoration: const BoxDecoration(
            border: Border(
                bottom: BorderSide(color: AppColors.border, width: 1))),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        child: Row(
          children: [
            ...List.generate(_rooms.length, (i) => _stripButton(i)),
            const Spacer(),
            IconButton(
              tooltip: _menuOpen ? 'Close rooms' : 'Open rooms',
              icon: StarIcon(
                  _menuOpen ? Icons.close_rounded : Icons.menu_rounded,
                  size: 19),
              onPressed: () => setState(() => _menuOpen = !_menuOpen),
            ),
          ],
        ),
      );

  Widget _stripButton(int i) {
    final room = _rooms[i];
    final active = _selected == i;
    final unread = _unread[room.$2] ?? 0;
    return Padding(
      padding: const EdgeInsets.only(right: 10),
      child: GestureDetector(
        onTap: () => setState(() => _selected = i),
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              width: 38,
              height: 38,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: active ? AppColors.primary.withValues(alpha: 0.16) : Colors.transparent,
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
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
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

  Widget _list() => ListView(
        padding: const EdgeInsets.all(8),
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 8),
            child: Text('MESSAGES',
                style: TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 10,
                    letterSpacing: 1.5)),
          ),
          ...List.generate(_rooms.length, (i) => _roomTile(i)),
        ],
      );

  Widget _roomTile(int i) {
    final name = _rooms[i].$1;
    final icon = _rooms[i].$3;
    final room = _rooms[i].$2;
    final unread = _unread[room] ?? 0;
    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      onTap: () => setState(() => _selected = i),
      child: ListTile(
        dense: true,
        visualDensity: VisualDensity.compact,
        leading: StarIcon(icon, size: 18),
        title: Text(name, style: const TextStyle(
            color: AppColors.textPrimary, fontSize: 12)),
        trailing: unread > 0
            ? Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: const BoxDecoration(
                    color: Color(0xFFFF4444), shape: BoxShape.circle),
                child: Text('$unread',
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        fontWeight: FontWeight.w700)),
              )
            : const Icon(Icons.chevron_right_rounded,
                color: AppColors.textMuted, size: 16),
      ),
    );
  }

  Widget _pane() =>
      GeneralChatScreen(room: _rooms[_selected].$2, title: _rooms[_selected].$1);
}
