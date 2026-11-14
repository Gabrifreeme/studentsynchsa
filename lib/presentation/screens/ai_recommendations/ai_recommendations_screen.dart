import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lipsyncstudent/core/theme/app_theme.dart';
import 'package:lipsyncstudent/presentation/providers/profile_provider.dart';
import 'package:lipsyncstudent/presentation/widgets/common_widgets.dart';
import 'package:lipsyncstudent/services/ai_service.dart';
import 'package:lipsyncstudent/domain/models/student_profile.dart';

class AiRecommendationsScreen extends ConsumerStatefulWidget {
  const AiRecommendationsScreen({super.key});

  @override
  ConsumerState<AiRecommendationsScreen> createState() =>
      _AiRecommendationsScreenState();
}

class _AiRecommendationsScreenState
    extends ConsumerState<AiRecommendationsScreen> {
  final List<_ChatMessage> _messages = [
    _ChatMessage(
      text:
          "Hi there! I'm ACEsi\n\n"
          "⭐ First things first — complete your profile so I can give you the best recommendations for your needs!",
      isUser: false,
    ),
  ];
  final _ctrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  bool _loading = false;

  void _maybeSetGreeting(StudentProfile? profile) {
    debugPrint('[AI_GREETING] profile=${profile == null ? "null" : "loaded"} firstName=${profile?.personal.firstName} subjectsLen=${profile?.grade12Subjects.length}');
    if (profile == null) return;
    if (profile.personal.firstName.isEmpty) return;
    final name = profile.personal.firstName;
    final isProfileComplete = profile.results.subjects.isNotEmpty;
    final greeting = isProfileComplete
        ? "Hi there $name! I'm ACEsi\n\n"
              "I can help you find the right university/bursary that fits your needs and style. "
              "I can do more than that - wherever you see me, just tap/click on me and ask away."
        : "Hi there $name! I'm ACEsi\n\n"
              "First things first - complete your profile so I can give you the best recommendations for your needs!";
    final currentGreeting = _messages.isNotEmpty ? _messages[0].text : '';
    if (currentGreeting == greeting) return;
    setState(() {
      if (_messages.isNotEmpty) {
        _messages[0] = _ChatMessage(text: greeting, isUser: false);
      } else {
        _messages.add(_ChatMessage(text: greeting, isUser: false));
      }
    });
  }


  Future<void> _sendMessage(String text) async {
    final profile = ref.read(profileProvider).valueOrNull;
    final userMsg = _ChatMessage(text: text, isUser: true);
    final acesiMsg = _ChatMessage(text: '', isUser: false);
    setState(() {
      _messages.add(userMsg);
      _messages.add(acesiMsg);
      _loading = true;
    });
    _scrollDown();

    final contextInfo = profile != null
        ? _buildProfileContext(profile)
        : '';


    await AiService.askStream(
      prompt:
          'You are ACEsi, a friendly South African university advisor. '
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

  String _buildProfileContext(StudentProfile p) {
    final symbolList = p.results.subjects.map((s) => '${s.subject} (${s.symbol})').where((s) => s.trim().isNotEmpty && !s.startsWith(' (')).join(', ');
    final aps = _computeApsFromSymbols(p.results.subjects);
    final interests = p.careerInterests.join(', ');
    final buffer = StringBuffer();
    buffer.write('STUDENT PROFILE (do not ask the student for this info again):\n');
    buffer.write('- Name: ${p.personal.firstName}\n');
    if (symbolList.isNotEmpty) buffer.write('- Grade 12 subjects + symbols: $symbolList\n');
    if (aps > 0) buffer.write('- Computed APS (best 6, excluding Life Orientation): $aps\n');
    if (p.address.province.isNotEmpty) buffer.write('- Province: ${p.address.province}\n');
    if (interests.isNotEmpty) buffer.write('- Career interests: $interests\n');
    if (p.status.bursaryRequired.isNotEmpty) buffer.write('- Needs funding: ${p.status.bursaryRequired}\n');
    return buffer.toString();
  }

  int _computeApsFromSymbols(List<SubjectDetail> subjects) {
    final points = <int>[];
    for (final s in subjects) {
      final sym = s.symbol.toUpperCase().trim();
      int p = 0;
      switch (sym) {
        case 'A': p = 7; break;
        case 'B': p = 6; break;
        case 'C': p = 5; break;
        case 'D': p = 4; break;
        case 'E': p = 3; break;
        case 'F': p = 2; break;
        case 'G': p = 1; break;
      }
      if (p > 0 && !s.subject.toLowerCase().contains('life orientation')) {
        points.add(p);
      }
    }
    points.sort((a, b) => b.compareTo(a));
    final best = points.take(6).toList();
    return best.fold(0, (a, b) => a + b);
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<StudentProfile?>>(profileProvider, (_, next) {
      _maybeSetGreeting(next.valueOrNull);
    });
    final loadedProfile = ref.watch(profileProvider).valueOrNull;
    if (loadedProfile != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _maybeSetGreeting(loadedProfile));
    }
    return Container(
      color: Colors.black,
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          centerTitle: true,
          title: const Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [StarAvatar(size: 28), SizedBox(width: 6), Text('ACEsi'), SizedBox(width: 6), StarAvatar(size: 28)],
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
                  if (i == 0 && _messages.length > 1 && !_messages[0].isUser) {
                    return const SizedBox.shrink();
                  }
                  final msg = _messages[i];
                  return _ChatBubble(message: msg);
                },
              ),
            ),
            Container(
              decoration: const BoxDecoration(
                color: AppColors.surface,
                border: Border(
                  top: BorderSide(color: AppColors.surfaceLight, width: 1),
                ),
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
                        hintText: 'Ask ACEsi anything...',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 10,
                        ),
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
                    icon: const Icon(
                      Icons.send_rounded,
                      color: AppColors.starGold,
                    ),
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
        mainAxisAlignment: message.isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            const SizedBox(width: 0), // removed left star
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
                  bottomLeft: Radius.circular(message.isUser ? 16 : 4),
                  bottomRight: Radius.circular(message.isUser ? 4 : 16),
                ),
              ),
              child: (message.text.contains('ACEsi') && !message.isUser)
                  ? RichText(
                      text: TextSpan(
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 14,
                          height: 1.5,
                        ),
                        children: [
                          ...(message.text.contains('⭐ ')
                            ? [TextSpan(text: message.text.split('⭐ ')[0]), 
                               WidgetSpan(alignment: PlaceholderAlignment.middle, child: StarAvatar(size: 16)),
                               TextSpan(text: ' ' + message.text.split('⭐ ')[1])]
                            : [TextSpan(text: message.text + ' ')]),
                          WidgetSpan(
                            alignment: PlaceholderAlignment.middle,
                            child: StarAvatar(size: 16),
                          ),
                        ],
                      ),
                    )
                  : Text(
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
