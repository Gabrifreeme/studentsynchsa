import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class GeneralChatScreen extends StatefulWidget {
  const GeneralChatScreen({super.key});

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

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _box = await Hive.openBox<String>('general_chat');
      final saved = _box!.values.toList();
      if (saved.isNotEmpty) {
        _messages.addAll(saved
            .map((s) => _ChatLine.fromJson(jsonDecode(s) as Map<String, dynamic>)));
      } else {
        _messages.add(_ChatLine(
          'Welcome to General Chat! Share a question, a win, or advice with '
          'students across South Africa. Your messages are saved on this device.',
          false,
        ));
        await _persist();
      }
    } catch (_) {
      _messages.add(_ChatLine('Chat could not load on this device.', false));
    }
    if (mounted) setState(() {});
  }

  Future<void> _persist() async {
    final box = _box;
    if (box == null) return;
    await box.clear();
    for (final m in _messages) {
      await box.add(jsonEncode(m.toJson()));
    }
  }

  void _send() {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    _ctrl.clear();
    setState(() => _messages.add(_ChatLine(text, true)));
    _persist();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 250),
            curve: Curves.easeOut);
      }
    });
  }

  @override
  void dispose() {
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
          title: const Text('General Chat'),
          actions: const [
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Center(
                child: Text('On this device',
                    style: TextStyle(
                        color: AppColors.textMuted, fontSize: 9)),
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
                        tooltip: 'Send message',
                        onPressed: _send,
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
