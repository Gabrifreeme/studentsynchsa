import 'dart:async';

import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/screens/chat/general_chat_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// Community opens with a left panel that really slides in and out.
/// The panel shows the room icons and the current chat list.
class ChatHomeScreen extends StatefulWidget {
  const ChatHomeScreen({super.key});

  @override
  State<ChatHomeScreen> createState() => _ChatHomeScreenState();
}

class _ChatHomeScreenState extends State<ChatHomeScreen>
    with SingleTickerProviderStateMixin {
  int _selected = 0; // General Chat is the open conversation
  bool _panelOpen = false;
  final Map<String, int> _unread = {};
  Timer? _poll;

  /// Explicit controller: AnimatedPositioned could not be relied on because
  /// the first open happened during the route transition and looked like a pop.
  late final AnimationController _panelController = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 450),
  );
  late final Animation<Offset> _panelSlide = Tween<Offset>(
    begin: const Offset(-1, 0),
    end: Offset.zero,
  ).animate(
    CurvedAnimation(parent: _panelController, curve: Curves.easeOutCubic),
  );

  static const _sampleChats = [
    ('Sipho Dlamini', 'Anyone applying to UCT this year?', '11:25', 2),
    ('Thandi Mokoena', 'NSFAS closes soon, check your profile', '10:42', 1),
    ('University Chat', 'Future classmates group is live', '09:15', 0),
  ];

  static const _rooms = [
    ('General Chat', 'general', Icons.forum_rounded),
    ('Province Base Chat', 'province', Icons.map_rounded),
    ('University Chat', 'university', Icons.school_rounded),
  ];

  @override
  void initState() {
    super.initState();
    // Wait for the dashboard-to-chat route transition, then slide in.
    Future<void>.delayed(const Duration(milliseconds: 500), () {
      if (mounted) _openPanel();
    });
    if (ChatService.isConfigured) {
      _checkUnread();
      _poll = Timer.periodic(const Duration(seconds: 5), (_) => _checkUnread());
    }
  }

  @override
  void dispose() {
    _poll?.cancel();
    _panelController.dispose();
    super.dispose();
  }

  void _openPanel() {
    if (!mounted) return;
    setState(() => _panelOpen = true);
    _panelController.forward();
  }

  void _closePanel() {
    if (!mounted) return;
    setState(() => _panelOpen = false);
    _panelController.reverse();
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
        ),
        // Scrim exists ONLY while the panel is open. An always-mounted
        // AbsorbPointer kept swallowing taps even when faded out, which made
        // the chat screen completely unresponsive after closing the panel.
        if (_panelOpen)
          Positioned.fill(
            child: GestureDetector(
              onTap: _closePanel,
              child: Container(color: Colors.black54),
            ),
          ),
        Positioned(
          left: 0,
          top: 0,
          bottom: 0,
          width: panelWidth,
          child: SlideTransition(
            position: _panelSlide,
            child: SizedBox(width: panelWidth, child: _panel()),
          ),
        ),
      ],
    );
  }

  /// Icons + permanently highlighted "Open chats" button under the title.
  Widget _topStrip() => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Tooltip(
              message: 'Open chats',
              child: GestureDetector(
                onTap: _openPanel,
                child: Container(
                  width: 36,
                  height: 36,
                  margin: const EdgeInsets.only(right: 6),
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    border: Border.all(color: AppColors.primary, width: 1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.menu_rounded,
                      size: 20, color: Colors.black),
                ),
              ),
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
          setState(() => _selected = i);
          _closePanel();
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
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children: List.generate(_rooms.length, (i) => _icon(i)),
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
        ),
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
