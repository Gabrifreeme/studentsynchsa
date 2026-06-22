import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/core/utils/offline_download.dart';

class OfflineTab extends StatelessWidget {
  final String universityId;

  const OfflineTab({
    super.key,
    required this.universityId,
  });

  @override
  Widget build(BuildContext context) {
    return _GuideCard(universityId: universityId);
  }
}

class _GuideCard extends StatelessWidget {
  final String universityId;
  const _GuideCard({required this.universityId});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => openAsset('assets/offline/guide.html'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.menu_book_rounded, color: AppColors.primary, size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'University Offline Guide',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Fees, deadlines, applications, accommodation, student life — all in one place',
                      style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.open_in_new, color: AppColors.textMuted, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}


