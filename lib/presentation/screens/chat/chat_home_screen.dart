import 'dart:async';

import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/chat/general_chat_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// WhatsApp-style chat home. The room panel is hidden until the menu button
/// is tapped. Each room shows an unread badge when new messages arrive.
class ChatHomeScreen extends StatefulWidget {
  const ChatHomeScreen({super.key});

  @override
  State<ChatHomeScreen> createState() => _ChatHomeScreenState();
}

class _ChatHomeScreenState extends State<ChatHomeScreen> {
  int? _selected;
  bool _menuOpen = false;
  final Map<String, int> _unread = {};
  Timer? _poll;

  static const _rooms = [
    ('General Chat', 'general', Icons.chat_rounded),
    ('Province-based', 'province', Icons.map_rounded),
    ('University Interest Groups', 'university', Icons.school_rounded),
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
        final count = rows.length;
        final read = ChatService.readCount(room.$2);
        if (!mounted) return;
        setState(() => _unread[room.$2] = count > read ? count - read : 0);
      } catch (_) {}
    }
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.of(context).size.width >= 700;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Community Chat'),
        leading: IconButton(
          tooltip: 'Open conversations',
          icon: const StarIcon(Icons.menu_rounded, size: 20),
          onPressed: () {
            if (wide) {
              setState(() => _menuOpen = !_menuOpen);
            } else {
              setState(() => _selected = null);
            }
          },
        ),
      ),
      body: wide ? _wideLayout() : (_selected == null ? _list() : _pane(_selected!)),
    );
  }

  Widget _wideLayout() {
    if (!_menuOpen) {
      return _selected == null
          ? const Center(
              child: Text('Tap the menu to open conversations',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 12)))
          : _pane(_selected!);
    }
    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(width: 260, child: _list()),
        const VerticalDivider(width: 1, color: AppColors.border),
        Expanded(
          child: _selected == null
              ? const Center(
                  child: Text('Select a conversation',
                      style: TextStyle(
                          color: AppColors.textMuted, fontSize: 12)))
              : _pane(_selected!),
        ),
      ],
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
    final active = _selected == i;
    final unread = _unread[room] ?? 0;
    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      onTap: () => _open(i),
      child: ListTile(
        dense: true,
        visualDensity: VisualDensity.compact,
        leading: StarIcon(icon, size: 18),
        title: Text(name,
            style: TextStyle(
                color: active ? AppColors.primary : AppColors.textPrimary,
                fontSize: 12)),
        trailing: unread > 0
            ? Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: const BoxDecoration(
                    color: AppColors.primary, shape: BoxShape.circle),
                child: Text('$unread',
                    style: const TextStyle(
                        color: Colors.black,
                        fontSize: 9,
                        fontWeight: FontWeight.w700)),
              )
            : const Icon(Icons.chevron_right_rounded,
                color: AppColors.textMuted, size: 16),
      ),
    );
  }

  void _open(int i) {
    final wide = MediaQuery.of(context).size.width >= 700;
    if (wide) {
      setState(() => _selected = i);
      return;
    }
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => GeneralChatScreen(room: _rooms[i].$2, title: _rooms[i].$1),
    ));
  }

  Widget _pane(int i) => GeneralChatScreen(room: _rooms[i].$2, title: _rooms[i].$1);
}
