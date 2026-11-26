import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/chat/general_chat_screen.dart';
import 'package:studentsyncsa/presentation/screens/notifications/notifications_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

/// WhatsApp-style chat home: a list panel on the left, conversation on the
/// right (desktop). On phones the list fills the screen and a tap opens the
/// conversation full-screen.
class ChatHomeScreen extends StatefulWidget {
  const ChatHomeScreen({super.key});

  @override
  State<ChatHomeScreen> createState() => _ChatHomeScreenState();
}

class _ChatHomeScreenState extends State<ChatHomeScreen> {
  int? _selected;
  static const _rooms = [
    ('General Chat', 'general', Icons.chat_rounded),
    ('Province-based', 'province', Icons.map_rounded),
    ('University Interest Groups', 'university', Icons.school_rounded),
  ];

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.of(context).size.width >= 700;
    return Scaffold(
      appBar: AppBar(title: const Text('Community Chat')),
      body: wide ? _wideLayout() : (_selected == null ? _list() : _pane(_selected!)),
    );
  }

  Widget _wideLayout() => Row(
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
          const SizedBox(height: 8),
          _notificationTile(),
        ],
      );

  Widget _roomTile(int i) {
    final name = _rooms[i].$1;
    final icon = _rooms[i].$3;
    final active = _selected == i;
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
        trailing: const Icon(Icons.chevron_right_rounded,
            color: AppColors.textMuted, size: 16),
      ),
    );
  }

  Widget _notificationTile() => AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        onTap: () {
          if (MediaQuery.of(context).size.width >= 700) {
            setState(() => _selected = 99);
          } else {
            Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => const NotificationsScreen()));
          }
        },
        child: const ListTile(
          dense: true,
          visualDensity: VisualDensity.compact,
          leading: StarIcon(Icons.notifications_none_rounded, size: 18),
          title: Text('Notifications',
              style: TextStyle(color: AppColors.textPrimary, fontSize: 12)),
          trailing: Icon(Icons.chevron_right_rounded,
              color: AppColors.textMuted, size: 16),
        ),
      );

  void _open(int i) {
    final wide = MediaQuery.of(context).size.width >= 700;
    if (wide) {
      setState(() => _selected = i);
      return;
    }
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => GeneralChatScreen(
        room: _rooms[i].$2,
        title: _rooms[i].$1,
      ),
    ));
  }

  Widget _pane(int i) {
    if (i == 99) return const NotificationsScreen();
    return GeneralChatScreen(room: _rooms[i].$2, title: _rooms[i].$1);
  }
}
