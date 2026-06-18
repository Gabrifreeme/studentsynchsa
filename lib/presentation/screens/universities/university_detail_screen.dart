import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/presentation/providers/university_provider.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';

class UniversityDetailScreen extends ConsumerWidget {
  final String universityId;
  const UniversityDetailScreen({super.key, required this.universityId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final universityAsync = ref.watch(universitiesProvider);
    final uni = universityAsync.valueOrNull?.where((u) => u.id == universityId).firstOrNull;

    if (uni == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('University Details')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: Text(uni.shortName)),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(uni.name,
                        style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary)),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.location_on_outlined,
                            size: 16, color: AppColors.textSecondary),
                        const SizedBox(width: 4),
                        Text(uni.province,
                            style: const TextStyle(color: AppColors.textSecondary)),
                      ],
                    ),
                    if (uni.description.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(uni.description,
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 13)),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Requirements Card
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Requirements',
                        style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary)),
                    const SizedBox(height: 12),
                    _ReqRow(Icons.check_circle_outline,
                        'Minimum APS: ${uni.minimumAps ?? "Not specified"}',
                        uni.minimumAps != null),
                    _ReqRow(Icons.monetization_on_outlined,
                        'Application Fee: ${uni.hasApplicationFee ? "R${uni.applicationFee?.toStringAsFixed(0) ?? ""}" : "No fee"}',
                        true),
                    _ReqRow(Icons.assignment_outlined,
                        'NBT Required: ${uni.requiresNbt ? "Yes" : "No"}',
                        true),
                    ...uni.requirements.map((r) => _ReqRow(
                        Icons.info_outline, r, true)),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Faculties
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Faculties',
                        style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary)),
                    const SizedBox(height: 12),
                    ...uni.faculties.map((f) => Padding(
                          padding: const EdgeInsets.only(bottom: 6),
                          child: Row(
                            children: [
                              const Icon(Icons.folder_outlined,
                                  size: 16, color: AppColors.primaryLight),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(f,
                                    style: const TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 13)),
                              ),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Action Buttons
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _launchUrl(uni.applicationUrl),
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Apply Now'),
                ),
              ),
              if (uni.website.isNotEmpty) ...[
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => _launchUrl(uni.website),
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

class _ReqRow extends StatelessWidget {
  final IconData icon;
  final String text;
  final bool met;
  const _ReqRow(this.icon, this.text, this.met);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 16, color: met ? AppColors.success : AppColors.textMuted),
          const SizedBox(width: 8),
          Expanded(
            child: Text(text,
                style: TextStyle(
                    color: met ? AppColors.textSecondary : AppColors.textMuted,
                    fontSize: 13)),
          ),
        ],
      ),
    );
  }
}
