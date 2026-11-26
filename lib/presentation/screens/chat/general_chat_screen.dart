import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:studentsyncsa/core/constants/app_constants.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

class GeneralChatScreen extends StatefulWidget {
  final String room;
  final String title;
  final Widget? topStrip;
  const GeneralChatScreen({
    super.key,
    this.room = 'general',
    this.title = 'General Chat',
    this.topStrip,
  });

  @override
  State<GeneralChatScreen> createState() => _GeneralChatScreenState();
}

class _ChatLine {
  final String text;
  final bool isUser;
  _ChatLine(this.text, this.isUser);

  Map<String, dynamic> toJson() => {'text': text, 'isUser': isUser};
  factory _ChatLine.fromJson(Map<String, dynamic> json) =>
      _ChatLine(json['text'] ?? '', json['isUser'] == true);
}

class _GeneralChatScreenState extends State<GeneralChatScreen> {
  final List<_ChatLine> _messages = [];
  final _ctrl = TextEditingController();
  final _scroll = ScrollController();
  Box<String>? _box;
  Timer? _poll;
  bool _busy = false;
  String? _error;

  bool get _live => ChatService.isConfigured;

  @override
  void initState() {
    super.initState();
    _load();
    if (_live) {
      _poll = Timer.periodic(const Duration(seconds: 4), (_) => _refresh());
    }
  }

  Future<void> _load() async {
    _box = await Hive.openBox<String>('general_chat');
    if (_live) {
      await _refresh();
    } else {
      final saved = _box!.values.toList();
      if (saved.isNotEmpty) {
        _messages.addAll(saved
            .map((s) => _ChatLine.fromJson(jsonDecode(s) as Map<String, dynamic>)));
      } else {
        _messages.add(_ChatLine(
          'Welcome to General Chat! Share a question, a win, or advice with '
          'students across South Africa. Messages are saved on this device.',
          false,
        ));
        await _persistLocal();
      }
    }
    if (mounted) setState(() {});
  }

  Future<void> _refresh() async {
    if (!_live || !mounted) return;
    try {
      final rows = await ChatService.fetchMessages(widget.room);
      if (!mounted) return;
      ChatService.markRead(widget.room, rows.length);
      setState(() {
        _error = null;
        _messages
          ..clear()
          ..addAll(rows.map((r) => _ChatLine(
                r['text'] ?? '',
                r['user_id'] == ChatService.myId,
              )));
      });
      _scrollToEnd();
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    }
  }

  Future<void> _persistLocal() async {
    final box = _box;
    if (box == null) return;
    await box.clear();
    for (final m in _messages) {
      await box.add(jsonEncode(m.toJson()));
    }
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250),
            curve: Curves.easeOut);
      }
    });
  }

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty || _busy) return;
    _ctrl.clear();

    if (_live) {
      final name = Hive.box<String>(AppConstants.settingsBox)
              .get('chatUserName') ??
          'Student';
      setState(() => _busy = true);
      try {
        await ChatService.sendMessage(text, name, widget.room);
        await _refresh();
      } catch (e) {
        if (mounted) setState(() => _error = '$e');
      } finally {
        if (mounted) setState(() => _busy = false);
      }
      return;
    }

    setState(() => _messages.add(_ChatLine(text, true)));
    _persistLocal();
    _scrollToEnd();
  }

  @override
  void dispose() {
    _poll?.cancel();
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(widget.title),
          actions: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Center(
                child: Text(_live ? 'Live · all students' : 'On this device',
                    style: TextStyle(
                        color: _live ? AppColors.success : AppColors.textMuted,
                        fontSize: 9)),
              ),
            ),
          ],
        ),
        body: Center(
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width < 600
                  ? double.infinity
                  : MediaQuery.of(context).size.width * 0.6,
            ),
            child: Column(
              children: [
                if (widget.topStrip != null)
                  Align(
                    alignment: Alignment.centerLeft,
                    child: widget.topStrip!,
                  ),
                if (_error != null)
                  Container(
                    width: double.infinity,
                    color: const Color(0xFF2A0000),
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 4),
                    child: Text(_error!,
                        maxLines: 2,
                        style: const TextStyle(
                            color: Colors.red, fontSize: 9)),
                  ),
                Expanded(
                  child: ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.all(10),
                    itemCount: _messages.length,
                    itemBuilder: (_, i) => _bubble(_messages[i]),
                  ),
                ),
                Container(
                  decoration: const BoxDecoration(
                    border: Border(
                        top: BorderSide(color: AppColors.border, width: 1)),
                  ),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 10, vertical: 6),
                  child: Row(
                    children: [
                      IconButton(
                        tooltip: 'Attach a file',
                        icon: const StarIcon(Icons.attach_file_rounded, size: 19),
                        onPressed: () => _soon('Attachments coming soon'),
                      ),
                      IconButton(
                        tooltip: 'Add an emoji',
                        icon: const StarIcon(Icons.emoji_emotions_outlined, size: 19),
                        onPressed: _showEmojiPicker,
                      ),
                      Expanded(
                        child: TextField(
                          controller: _ctrl,
                          minLines: 1,
                          maxLines: 3,
                          style: const TextStyle(
                              color: AppColors.textPrimary, fontSize: 12),
                          decoration: const InputDecoration(
                            hintText: 'Write a message...',
                            hintStyle: TextStyle(
                                color: AppColors.textMuted, fontSize: 11),
                            border: InputBorder.none,
                          ),
                          onSubmitted: (_) => _send(),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Voice message',
                        icon: const StarIcon(Icons.mic_none_rounded, size: 19),
                        onPressed: () => _soon('Voice messages coming soon'),
                      ),
                      IconButton(
                        tooltip: 'Send message',
                        onPressed: _busy ? null : _send,
                        icon: const StarIcon(Icons.send_rounded, size: 20),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }


  void _soon(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: AppColors.surfaceLight),
    );
  }

  void _showEmojiPicker() {
    const emojis = ['😀', '😂', '😍', '👍', '🙌', '🎉', '🔥', '❤️', '⭐', '✅', '🙏', '💯'];
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(10),
        child: Wrap(
          spacing: 6,
          runSpacing: 6,
          children: emojis
              .map((e) => InkWell(
                    onTap: () {
                      _ctrl.text = '$_ctrl.text$e';
                      _ctrl.selection = TextSelection.collapsed(offset: _ctrl.text.length);
                      Navigator.pop(ctx);
                    },
                    child: Container(
                      width: 38,
                      height: 38,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.border),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(e, style: const TextStyle(fontSize: 20)),
                    ),
                  ))
              .toList(),
        ),
      ),
    );
  }

  Widget _bubble(_ChatLine m) {
    return Align(
      alignment: m.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: AppCard(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 280),
          child: Text(
            m.text,
            style: TextStyle(
                color: m.isUser ? AppColors.primary : AppColors.textSecondary,
                fontSize: 11),
          ),
        ),
      ),
    );
  }
}
