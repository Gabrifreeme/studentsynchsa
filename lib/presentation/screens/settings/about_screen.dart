import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text('About Us')),
        body: Center(
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.7,
            ),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(AppSpaces.lg),
              child: Column(
                children: [
                  const StarAvatar(size: 72, pulse: true),
                  const SizedBox(height: AppSpaces.lg),
                  const Text(
                    'LibSyncStudent',
                    style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 13,
                        fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: AppSpaces.sm),
                  const Text(
                    'Made for South African Students',
                    style: TextStyle(
                        color: AppColors.textSecondary, fontSize: 9),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppSpaces.xl),
                  AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        _AboutRow('Version', '1.0.0'),
                        _AboutRow('Powered by', 'ACEsi'),
                        _AboutRow('Assistant', 'Star'),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _AboutRow extends StatelessWidget {
  final String label;
  final String value;
  const _AboutRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpaces.xs),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 9)),
          Text(value,
              style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 9)),
        ],
      ),
    );
  }
}
