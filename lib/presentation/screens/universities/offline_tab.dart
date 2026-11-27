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
        borderRadius: BorderRadius.circular(8),
        onTap: () => openAsset(
            'assets/offline/guides/$universityId.html'),
        child: Padding(
          padding: const EdgeInsets.all(11),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.menu_book_rounded, color: AppColors.primary, size: 24),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'University Offline Guide',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Fees, deadlines, applications, accommodation, student life — all in one place',
                      style: TextStyle(fontSize: 9, color: AppColors.textSecondary),
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


