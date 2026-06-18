import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/data/datasources/mock_bursary_data.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';

class FundingListScreen extends StatelessWidget {
  const FundingListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final bursaries = MockBursaryData.all;

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text('Funding & Bursaries')),
        body: ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: bursaries.length,
          itemBuilder: (_, i) {
            final b = bursaries[i];
            final isUrgent = b.deadline != null &&
                b.deadline!.difference(DateTime.now()).inDays < 60;
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: AppCard(
                onTap: () => context.push('/funding/${b.id}'),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(b.name,
                              style: const TextStyle(
                                  color: AppColors.textPrimary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 15)),
                        ),
                        if (isUrgent)
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.error.withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: const Text('DEADLINE SOON',
                                style: TextStyle(
                                    color: AppColors.error,
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold)),
                          ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(b.provider,
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 12)),
                    const SizedBox(height: 8),
                    Text(b.description,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: AppColors.textMuted, fontSize: 12)),
                    if (b.deadline != null) ...[
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.calendar_today_outlined,
                              size: 12, color: AppColors.textMuted),
                          const SizedBox(width: 4),
                          Text(
                              'Deadline: ${_formatDate(b.deadline!)}',
                              style: const TextStyle(
                                  color: AppColors.textMuted, fontSize: 11)),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
}
