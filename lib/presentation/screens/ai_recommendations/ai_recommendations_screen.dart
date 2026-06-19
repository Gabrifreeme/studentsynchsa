import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/ai_service.dart';

class AiRecommendationsScreen extends ConsumerStatefulWidget {
  const AiRecommendationsScreen({super.key});

  @override
  ConsumerState<AiRecommendationsScreen> createState() =>
      _AiRecommendationsScreenState();
}

class _AiRecommendationsScreenState
    extends ConsumerState<AiRecommendationsScreen> {
  List<_ChatMessage> _messages = [
    _ChatMessage(
      text: "Hi there! I'm Star ⭐\n\n"
          "First things first — complete your profile so I can give you the best recommendations for your needs!",
      isUser: false,
    ),
  ];
  final _ctrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _loading = false;
  bool _initialAsked = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final profile = ref.read(profileProvider).valueOrNull;
      final name = profile?.personal.firstName.isNotEmpty == true ? profile!.personal.firstName : 'there';
      final isProfileComplete = profile != null && profile.personal.firstName.isNotEmpty &&
          profile.grade12Subjects.isNotEmpty;
      final greeting = isProfileComplete
          ? "Hi there $name! I'm Star ⭐\n\n"
              "I can help you find the right university/bursary that fits your needs and style. "
              "I can do more than that — wherever you see me, just tap/click on me and ask away."
          : "Hi there $name! I'm Star ⭐\n\n"
              "First things first — complete your profile so I can give you the best recommendations for your needs!";
      if (_messages.isNotEmpty && !_messages.first.text.contains(name)) {
        setState(() {
          _messages[0] = _ChatMessage(text: greeting, isUser: false);
        });
      }
    });
  }

  Future<void> _sendMessage(String text) async {
    final profile = ref.read(profileProvider).valueOrNull;
    final userMsg = _ChatMessage(text: text, isUser: true);
    final starMsg = _ChatMessage(text: '', isUser: false);
    setState(() {
      _messages.add(userMsg);
      _messages.add(starMsg);
      _loading = true;
    });
    _scrollDown();

    final contextInfo = profile != null
        ? 'The student is ${profile.personal.firstName}, studying ${profile.grade12Subjects.map((s) => s.subject).join(", ")}, APS: ${profile.apsScore}, interested in ${profile.careerInterests.join(", ")}.'
        : '';

    await AiService.askStream(
      prompt: 'You are Star, a friendly South African university advisor. '
          'Keep answers warm, encouraging, and practical (2-3 sentences max per point).\n'
          '$contextInfo\nStudent asks: $text',
      onToken: (token) {
        setState(() {
          _messages.last = _ChatMessage(
            text: _messages.last.text + token,
            isUser: false,
          );
        });
        _scrollDown();
      },
    );

    setState(() => _loading = false);
  }

  Future<void> _askInitial() async {
    final profile = ref.read(profileProvider).valueOrNull;
    if (profile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Complete your profile first so Star can help you!'),
          backgroundColor: AppColors.warning,
        ),
      );
      return;
    }

    final subjects = profile.grade12Subjects.isNotEmpty
        ? profile.grade12Subjects.map((s) => '${s.subject} (${s.mark}%)').toList()
        : profile.grade11Subjects.map((s) => '${s.subject} (${s.mark}%)').toList();

    final prompt = AiService.buildPrompt(
      firstName: profile.personal.firstName,
      apsScore: profile.apsScore,
      subjects: subjects,
      careerInterests: profile.careerInterests,
      province: profile.address.province,
    );

    final starMsg = _ChatMessage(text: '', isUser: false);
    setState(() {
      _messages.add(starMsg);
      _initialAsked = true;
      _loading = true;
    });

    await AiService.askStream(
      prompt: prompt,
      onToken: (token) {
        setState(() {
          _messages.last = _ChatMessage(
            text: _messages.last.text + token,
            isUser: false,
          );
        });
        _scrollDown();
      },
    );

    setState(() => _loading = false);
  }

  void _scrollDown() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              StarAvatar(size: 28),
              SizedBox(width: 8),
              Text('Star'),
            ],
          ),
        ),
        body: Column(
          children: [
            Expanded(
              child: ListView.builder(
                      controller: _scrollCtrl,
                      padding: const EdgeInsets.all(16),
                      itemCount: _messages.length,
                      itemBuilder: (context, i) {
                        final msg = _messages[i];
                        return _ChatBubble(message: msg);
                      },
                    ),
            ),
            Container(
              decoration: const BoxDecoration(
                color: AppColors.surface,
                border: Border(
                    top: BorderSide(color: AppColors.surfaceLight, width: 1)),
              ),
              padding: EdgeInsets.only(
                left: 12,
                right: 12,
                top: 8,
                bottom: MediaQuery.of(context).padding.bottom + 8,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _ctrl,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _loading
                          ? null
                          : (v) {
                              if (v.trim().isNotEmpty) {
                                _sendMessage(v.trim());
                                _ctrl.clear();
                              }
                            },
                      decoration: const InputDecoration(
                        hintText: 'Ask Star anything...',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(
                            horizontal: 16, vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: _loading
                        ? null
                        : () {
                            if (_ctrl.text.trim().isNotEmpty) {
                              _sendMessage(_ctrl.text.trim());
                              _ctrl.clear();
                            }
                          },
                    icon: const Icon(Icons.send_rounded,
                        color: AppColors.starGold),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatMessage {
  final String text;
  final bool isUser;
  const _ChatMessage({required this.text, required this.isUser});
}

class _ChatBubble extends StatelessWidget {
  final _ChatMessage message;
  const _ChatBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            const StarAvatar(size: 28),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: message.isUser
                    ? AppColors.primary.withValues(alpha: 0.2)
                    : AppColors.card,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(
                      message.isUser ? 16 : 4),
                  bottomRight: Radius.circular(
                      message.isUser ? 4 : 16),
                ),
              ),
              child: Text(
                message.text,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 14,
                  height: 1.5,
                ),
              ),
            ),
          ),
          if (message.isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }
}
