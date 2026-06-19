import 'package:flutter/material.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/core/utils/offline_download.dart';
import 'package:studentsynchsa/domain/models/offline_resource.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';

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
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Offline Resources',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'These resources are bundled with the app. Tap Download to save a copy to your device for offline viewing.',
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        if (resources.isEmpty)
          const Padding(
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
          )
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            itemCount: resources.length,
            itemBuilder: (ctx, i) {
              final r = resources[i];
              return Card(
                margin: const EdgeInsets.symmetric(vertical: 8),
                child: ListTile(
                  leading: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(_iconForType(r.type), color: AppColors.primary, size: 20),
                  ),
                  title: Text(r.title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                  subtitle: r.description != null
                      ? Text(r.description!, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))
                      : null,
                  trailing: ElevatedButton.icon(
                    onPressed: () => _openResource(context, r),
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
            },
          ),
      ],
    );
  }

  void _openResource(BuildContext context, OfflineResource resource) {
    downloadAsset(resource.assetPath);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Downloading ${resource.title}...'),
        backgroundColor: AppColors.primary,
        behavior: SnackBarBehavior.floating,
        duration: const Duration(seconds: 2),
      ),
    );
  }
}

IconData _iconForType(String type) {
  switch (type) {
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
