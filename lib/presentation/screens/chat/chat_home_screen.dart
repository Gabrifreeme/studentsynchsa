import 'dart:async';

import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/chat/general_chat_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// Community chat. The room panel is a real Flutter Drawer, so it gets the
/// built-in left-to-right slide animation and scrim instead of a hand-rolled
/// transform that could appear to "pop" open.
class ChatHomeScreen extends StatefulWidget {
  const ChatHomeScreen({super.key});

  @override
  State<ChatHomeScreen> createState() => _ChatHomeScreenState();
}

class _ChatHomeScreenState extends State<ChatHomeScreen> {
  final _scaffoldKey = GlobalKey<ScaffoldState>();
  int _selected = 0; // General Chat is the open conversation
  final Map<String, int> _unread = {};
  Timer? _poll;

  // Example badge counts shown on the room icons for the build demo.
  static const _demoUnread = {'province': 2, 'university': 3};

  /// Current and history chats only - no "University Chat" entry.
  static const _sampleChats = [
    ('Sipho Dlamini', 'Anyone applying to UCT this year?', '11:25', 2),
    ('Thandi Mokoena', 'NSFAS closes soon, check your profile', '10:42', 1),
    ('Lerato Nkosi', 'See you at registration!', '09:15', 0),
    ('Kabelo Sithole', 'Sent you the NSFAS checklist', 'Yesterday', 0),
  ];

  static const _rooms = [
    ('General Chat', 'general', Icons.forum_rounded),
    ('Province Base Chat', 'province', Icons.map_rounded),
    ('University Chat', 'university', Icons.school_rounded),
  ];

  @override
  void initState() {
    super.initState();
    // Let the dashboard route transition finish, then slide the panel in.
    Future<void>.delayed(const Duration(milliseconds: 600), () {
      if (mounted) _scaffoldKey.currentState?.openDrawer();
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

  void _openDrawer() => _scaffoldKey.currentState?.openDrawer();

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

  int _badgeCount(String room) =>
      _demoUnread[room] ?? _unread[room] ?? 0;

  @override
  Widget build(BuildContext context) {
    final w = MediaQuery.of(context).size.width;
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: Colors.black,
      drawer: Drawer(
        width: w < 600 ? w * 0.82 : 300.0,
        backgroundColor: const Color(0xFF080808),
        child: _panel(),
      ),
      body: GeneralChatScreen(
        room: _rooms[_selected].$2,
        title: _rooms[_selected].$1,
        topStrip: _topStrip(),
      ),
    );
  }

  /// Icons + permanently highlighted multicolour "Open chats" button.
  Widget _topStrip() => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            GestureDetector(
              onTap: _openDrawer,
              child: Container(
                width: 36,
                height: 36,
                margin: const EdgeInsets.only(right: 6),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.18),
                  border: Border.all(color: AppColors.primary, width: 2),
                  borderRadius: BorderRadius.circular(10),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.35),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: const StarIcon(Icons.menu_rounded, size: 20),
              ),
            ),
            ...List.generate(_rooms.length, (i) => _icon(i)),
          ],
        ),
      );

  Widget _icon(int i, {bool fromPanel = false}) {
    final room = _rooms[i];
    final active = _selected == i;
    final unread = _badgeCount(room.$2);
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: GestureDetector(
        onTap: () {
          if (!mounted) return;
          setState(() => _selected = i);
          if (fromPanel && mounted && Navigator.of(context).canPop()) {
            Navigator.of(context).pop();
          }
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

  Widget _panel() => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 16, 12, 10),
            child: Text(
              'CHATS',
              style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 10,
                  letterSpacing: 1.5),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: List.generate(
                  _rooms.length, (i) => _icon(i, fromPanel: true)),
            ),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(8),
              children:
                  List.generate(_sampleChats.length, (i) => _sampleTile(i)),
            ),
          ),
        ],
      );

  Widget _sampleTile(int i) {
    final c = _sampleChats[i];
    return AppCard(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: ListTile(
        dense: true,
        visualDensity: VisualDensity.compact,
        leading: CircleAvatar(
          radius: 14,
          backgroundColor: AppColors.primaryDark,
          child: Text(c.$1[0],
              style: const TextStyle(color: AppColors.primary, fontSize: 11)),
        ),
        title: Text(c.$1,
            style: const TextStyle(color: AppColors.textPrimary, fontSize: 11)),
        subtitle: Text(c.$2,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: AppColors.textMuted, fontSize: 9)),
        trailing: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(c.$3,
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 8)),
            if (c.$4 > 0) _badge(c.$4),
          ],
        ),
      ),
    );
  }
}
