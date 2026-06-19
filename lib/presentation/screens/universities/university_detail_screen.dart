import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/core/utils/pdf_download.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/providers/university_provider.dart';
import 'package:studentsyncsa/presentation/screens/universities/offline_tab.dart';
import 'package:studentsyncsa/presentation/screens/universities/application_form_screen.dart';
import 'package:studentsyncsa/presentation/screens/universities/university_webview_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/pdf_generator.dart';


class UniversityDetailScreen extends ConsumerWidget {
  final String universityId;
  final String initialTab;
  const UniversityDetailScreen({super.key, required this.universityId, this.initialTab = ''});

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
              if (initialTab != 'offline') ...[
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

                // Contact & Social
                if (uni.phone.isNotEmpty || uni.email.isNotEmpty || uni.address.isNotEmpty || uni.socialMedia.isNotEmpty)
                  AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Contact & Social',
                            style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary)),
                        if (uni.address.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          _ContactRow(Icons.location_on_outlined, uni.address.replaceAll(', ', '\n')),
                        ],
                        if (uni.phone.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          _ContactRow(Icons.phone_outlined, uni.phone, onTap: () => _launchUrl('tel:${uni.phone.replaceAll(RegExp(r'\s+'), '')}')),
                        ],
                        if (uni.email.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          _ContactRow(Icons.email_outlined, uni.email, onTap: () => _launchUrl('mailto:${uni.email}')),
                        ],
                        if (uni.socialMedia.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          const Divider(height: 1, color: AppColors.surfaceLight),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: uni.socialMedia.entries.map((e) {
                              IconData icon;
                              Color iconColor;
                              switch (e.key.toLowerCase()) {
                                case 'facebook':
                                  icon = Icons.facebook;
                                  iconColor = const Color(0xFF1877F2);
                                  break;
                                case 'linkedin':
                                  icon = Icons.link;
                                  iconColor = const Color(0xFF0A66C2);
                                  break;
                                case 'twitter':
                                  icon = Icons.alternate_email;
                                  iconColor = const Color(0xFF1DA1F2);
                                  break;
                                case 'instagram':
                                  icon = Icons.camera_alt_outlined;
                                  iconColor = const Color(0xFFE4405F);
                                  break;
                                case 'youtube':
                                  icon = Icons.play_circle_outline;
                                  iconColor = const Color(0xFFFF0000);
                                  break;
                                default:
                                  icon = Icons.link;
                                  iconColor = AppColors.primary;
                              }
                              return ActionChip(
                                avatar: Icon(icon, size: 16, color: iconColor),
                                label: Text(e.key,
                                    style: const TextStyle(fontSize: 12)),
                                onPressed: () => _launchUrl(e.value),
                              );
                            }).toList(),
                          ),
                        ],
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

                // ✨ Apply (in-app form)
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => ApplicationFormScreen(university: uni),
                        ),
                      );
                    },
                    icon: const Icon(Icons.auto_awesome_rounded),
                    label: const Text('✨ Apply'),
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      backgroundColor: AppColors.primary,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    if (uni.applicationUrl.isNotEmpty)
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => UniversityWebViewScreen(
                                  url: uni.applicationUrl,
                                  universityName: uni.shortName,
                                ),
                              ),
                            );
                          },
                          icon: const Icon(Icons.open_in_new, size: 18),
                          label: const Text('↗ Online Portal'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                    if (uni.applicationUrl.isNotEmpty && uni.website.isNotEmpty)
                      const SizedBox(width: 8),
                    if (uni.website.isNotEmpty)
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () => _launchUrl(uni.website),
                          icon: const Icon(Icons.language, size: 18),
                          label: const Text('Website'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                  ],
                ),
              ],

              // Offline Resources section
              if (initialTab == 'offline') ...[
                const SizedBox(height: 8),
                AppCard(
                  child: OfflineTab(
                    universityId: uni.id,
                    resources: uni.offlineResources,
                  ),
                ),
              ],

              // Tools section (PDF + Copy)
              const SizedBox(height: 8),
              AppCard(
                child: Row(
                  children: [
                    Expanded(
                      child: _toolButton(
                        icon: Icons.picture_as_pdf,
                        label: 'PDF',
                        onTap: () => _generatePdf(context, ref, uni.shortName),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: _toolButton(
                        icon: Icons.content_copy,
                        label: 'Copy Helper',
                        onTap: () => context.push('/universities/${uni.id}/helper?name=${Uri.encodeComponent(uni.shortName)}'),
                      ),
                    ),
                  ],
                ),
              ),

              // Tab switcher at bottom
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: _buildTab(
                      label: 'Details',
                      icon: Icons.info_outline,
                      selected: initialTab != 'offline',
                      onTap: () => context.pushReplacement('/universities/${uni.id}'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildTab(
                      label: 'Offline Resources',
                      icon: Icons.download_rounded,
                      selected: initialTab == 'offline',
                      onTap: () => context.pushReplacement('/universities/${uni.id}?tab=offline'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTab({
    required String label,
    required IconData icon,
    required bool selected,
    required VoidCallback onTap,
  }) {
    final color = selected ? AppColors.primary : AppColors.textSecondary;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
        decoration: BoxDecoration(
          color: selected ? AppColors.primary.withValues(alpha: 0.12) : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: color,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _toolButton({required IconData icon, required String label, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Icon(icon, size: 20, color: AppColors.primaryLight),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 10, color: AppColors.textSecondary)),
          ],
        ),
      ),
    );
  }

  Future<void> _generatePdf(BuildContext context, WidgetRef ref, String uniName) async {
    final profile = ref.read(profileProvider).valueOrNull;
    if (profile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Complete your profile first'), backgroundColor: AppColors.error),
      );
      return;
    }
    try {
      final bytes = await PdfGenerator().generateApplicationPdf(profile, universityName: uniName);
      downloadPdfBytes(bytes, '${uniName.replaceAll(RegExp(r'\s+'), '_')}_Application.pdf');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('PDF generated!'), backgroundColor: AppColors.success),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed: $e'), backgroundColor: AppColors.error),
      );
    }
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

class _ContactRow extends StatelessWidget {
  final IconData icon;
  final String text;
  final VoidCallback? onTap;
  const _ContactRow(this.icon, this.text, {this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          children: [
            Icon(icon, size: 18, color: AppColors.primary),
            const SizedBox(width: 10),
            Expanded(
              child: Text(text,
                  style: const TextStyle(
                      color: AppColors.textSecondary, fontSize: 13)),
            ),
            if (onTap != null)
              const Icon(Icons.open_in_new, size: 14, color: AppColors.textMuted),
          ],
        ),
      ),
    );
  }
}
