import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/core/utils/offline_download.dart';
import 'package:studentsyncsa/domain/models/offline_resource.dart';

class OfflineTab extends StatelessWidget {
  final String universityId;
  final List<OfflineResource> resources;

  const OfflineTab({
    super.key,
    required this.universityId,
    required this.resources,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _GuideCard(universityId: universityId),
        const SizedBox(height: 8),
        const Text(
          'University Resources',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 6),
        const Text(
          'View the official university page live, or download PDFs for offline use.',
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 12),
        if (resources.isEmpty)
          const _EmptyState()
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: resources.length,
            itemBuilder: (ctx, i) => _ResourceTile(resource: resources[i]),
          ),
      ],
    );
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

class _ResourceTile extends StatelessWidget {
  final OfflineResource resource;
  const _ResourceTile({required this.resource});

  bool get _isPage => resource.type == 'page';

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(_iconForType(resource.type), color: AppColors.primary, size: 20),
        ),
        title: Text(resource.title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
        subtitle: resource.description != null
            ? Text(resource.description!, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))
            : null,
        trailing: _isPage
            ? ElevatedButton.icon(
                onPressed: () => _openPage(context),
                icon: const Icon(Icons.open_in_new, size: 16),
                label: const Text('View'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                ),
              )
            : ElevatedButton.icon(
                onPressed: () => _downloadResource(context),
                icon: const Icon(Icons.download, size: 16),
                label: const Text('Download'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                ),
              ),
      ),
    );
  }

  Future<void> _openPage(BuildContext context) async {
    await openAsset(resource.assetPath);
  }

  Future<void> _downloadResource(BuildContext context) async {
    await downloadAsset(resource.assetPath);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('${resource.title} saved to device'),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(32),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off, size: 48, color: AppColors.textMuted),
            SizedBox(height: 12),
            Text(
              'No offline resources available',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
            ),
            SizedBox(height: 4),
            Text(
              'Resources will appear here when added',
              style: TextStyle(color: AppColors.textMuted, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}

IconData _iconForType(String type) {
  switch (type) {
    case 'page':
      return Icons.language;
    case 'pdf':
      return Icons.picture_as_pdf;
    case 'image':
      return Icons.image;
    case 'map':
      return Icons.map;
    case 'doc':
      return Icons.description;
    default:
      return Icons.file_present;
  }
}
