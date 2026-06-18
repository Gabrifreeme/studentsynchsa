import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/presentation/providers/profile_provider.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';
import 'package:studentsynchsa/services/ai_service.dart';

class AiRecommendationsScreen extends ConsumerStatefulWidget {
  const AiRecommendationsScreen({super.key});

  @override
  ConsumerState<AiRecommendationsScreen> createState() =>
      _AiRecommendationsScreenState();
}

class _AiRecommendationsScreenState
    extends ConsumerState<AiRecommendationsScreen> {
  String? _response;
  bool _loading = false;
  bool _hasAsked = false;

  Future<void> _askStar() async {
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

    setState(() {
      _loading = true;
      _response = null;
    });

    final subjects = profile.grade12Subjects.isNotEmpty
        ? profile.grade12Subjects.map((s) => '${s.subject} (${s.mark}%)').toList()
        : profile.grade11Subjects.map((s) => '${s.subject} (${s.mark}%)').toList();

    final prompt = AiService.buildPrompt(
      firstName: profile.firstName,
      apsScore: profile.apsScore,
      subjects: subjects,
      careerInterests: profile.careerInterests,
      province: profile.province,
    );

    final result = await AiService.ask(prompt);
    setState(() {
      _response = result;
      _loading = false;
      _hasAsked = true;
    });
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
              Text('Star Recommendations'),
            ],
          ),
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              // Star Welcome
              AppCard(
                child: Column(
                  children: [
                    const StarAvatar(size: 72, pulse: true),
                    const SizedBox(height: 16),
                    const Text(
                      "Hi! I'm Star ⭐",
                      style: TextStyle(
                        color: AppColors.starGold,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Your smart university guide. I can help you find the perfect universities based on your profile, marks, and interests.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                          color: AppColors.textSecondary, fontSize: 14),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Ask Button
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _loading ? null : _askStar,
                  icon: _loading
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.auto_awesome_rounded),
                  label: Text(_loading
                      ? 'Star is thinking...'
                      : _hasAsked
                          ? 'Ask Star Again'
                          : 'Ask Star for Recommendations'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.starGold,
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Response
              if (_response != null)
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          StarAvatar(size: 24),
                          SizedBox(width: 8),
                          Text('Star says:',
                              style: TextStyle(
                                  color: AppColors.starGold,
                                  fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _response!,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 14,
                          height: 1.6,
                        ),
                      ),
                    ],
                  ),
                ),

              if (_response != null &&
                  (_response!.contains('offline') ||
                      _response!.contains('error')))
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.warning.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                          color: AppColors.warning.withValues(alpha: 0.3)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.info_outline,
                            color: AppColors.warning, size: 16),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Run "ollama serve" in a terminal to wake Star up!',
                            style: TextStyle(
                                color: AppColors.warning, fontSize: 12),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
