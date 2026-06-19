import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/datasources/mock_bursary_data.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class FundingDetailScreen extends StatelessWidget {
  final String bursaryId;
  const FundingDetailScreen({super.key, required this.bursaryId});

  @override
  Widget build(BuildContext context) {
    final bursary = MockBursaryData.all.where((b) => b.id == bursaryId).firstOrNull;

    if (bursary == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Funding Details')),
        body: const Center(child: Text('Not found')),
      );
    }

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: Text(bursary.name)),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(bursary.name,
                        style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary)),
                    const SizedBox(height: 4),
                    Text(bursary.provider,
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 14)),
                    if (bursary.coverage.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      const Text('Coverage',
                          style: TextStyle(
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text(bursary.coverage,
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 13)),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 16),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Description',
                        style: TextStyle(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(bursary.description,
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 13)),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Eligibility',
                        style: TextStyle(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text(bursary.eligibility,
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 13)),
                    if (bursary.fieldsOfStudy.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      const Text('Fields of Study',
                          style: TextStyle(
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      ...bursary.fieldsOfStudy.map((f) => Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Row(
                              children: [
                                const Icon(Icons.check_circle_outline,
                                    size: 14, color: AppColors.success),
                                const SizedBox(width: 8),
                                Text(f,
                                    style: const TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 12)),
                              ],
                            ),
                          )),
                    ],
                    if (bursary.deadline != null) ...[
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          const Icon(Icons.calendar_today_outlined,
                              size: 16, color: AppColors.warning),
                          const SizedBox(width: 8),
                          Text(
                            'Deadline: ${bursary.deadline!.day}/${bursary.deadline!.month}/${bursary.deadline!.year}',
                            style: const TextStyle(
                                color: AppColors.warning,
                                fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _launchUrl(bursary.applicationUrl),
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Apply Now'),
                ),
              ),
              if (bursary.website.isNotEmpty) ...[
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => _launchUrl(bursary.website),
                    icon: const Icon(Icons.language),
                    label: const Text('Visit Website'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  void _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }
}
