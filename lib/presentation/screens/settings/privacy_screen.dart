import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class PrivacyScreen extends StatelessWidget {
  const PrivacyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text('Privacy & Compliance')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // 1. Privacy Commitment
            _Section(
              icon: Icons.shield_rounded,
              title: 'Privacy Notice',
              children: [
                'studentsyncsa respects your privacy. We collect only what you choose to share, use it solely to help you apply to South African universities and bursaries, and never sell your data.',
                'Your data stays on your device by default. When you apply, information is shared only with the institution you choose. This notice explains what we collect, why, and your rights.',
              ],
            ),
            const SizedBox(height: 16),

            // 2. Data Rights Requests
            _Section(
              icon: Icons.assignment_turned_in_outlined,
              title: 'Your Data Rights',
              children: [
                'Under POPIA (South Africa) and applicable law, you have the right to:',
                '• Access — request a copy of the data we hold about you',
                '• Correction — update or fix inaccurate information',
                '• Deletion — request removal of your data (right to be forgotten)',
                '• Restrict — limit how we process your data',
                '• Portability — receive your data in a transferable format',
                '• Object — object to processing for specific purposes',
                'To exercise any of these rights, email us at privacy@studentsyncsa.app. We will respond within 72 hours.',
              ],
            ),
            const SizedBox(height: 16),

            // 3. Cookies & Tracking
            _Section(
              icon: Icons.cookie_outlined,
              title: 'Cookies & Tracking',
              children: [
                'studentsyncsa does not use cookies or tracking scripts in the app. We do not serve ads, embed third-party trackers, or build behavioural profiles.',
                'When you visit our website (studentsyncsa.app), we may use essential cookies for site functionality and anonymous analytics (page views, browser type) to improve the site. No personal data is collected through these cookies.',
                'Third-party links (university websites, bursary portals) have their own cookie policies. We recommend reviewing them separately.',
              ],
            ),
            const SizedBox(height: 16),

            // 4. Data Security
            _Section(
              icon: Icons.lock_outline,
              title: 'Data Security Measures',
              children: [
                'Local Storage: Your profile and application data are stored in encrypted local storage (Hive) on your device. No cloud storage is used unless you explicitly enable sync.',
                'No External Servers: studentsyncsa does not maintain a central database of user profiles. Your data stays with you.',
                'Encryption: Any data transmitted during application submissions uses HTTPS/TLS encryption. Future cloud sync features will use end-to-end encryption.',
                'Authentication: The app uses anonymous local authentication. No passwords or biometric data are transmitted or stored externally.',
                'Regular Audits: We review our data practices regularly to ensure compliance with POPIA and evolving privacy best practices.',
              ],
            ),
            const SizedBox(height: 16),

            // 5. Contact Point
            _Section(
              icon: Icons.mail_outline,
              title: 'Privacy Contact',
              children: [
                'For all privacy-related inquiries, data rights requests, or concerns, contact our designated privacy contact:',
              ],
              trailing: Padding(
                padding: const EdgeInsets.only(top: 12),
                child: AppCard(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _ContactLine(label: 'Data Protection', value: 'Privacy Team'),
                        _ContactLine(label: 'Email', value: 'privacy@studentsyncsa.app'),
                        _ContactLine(label: 'Response time', value: 'Within 72 hours'),
                        const SizedBox(height: 8),
                        const Text(
                          'Or use the Settings → Clear All Local Data option to remove all stored information immediately.',
                          style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Consent Banners & Granular Options
            _Section(
              icon: Icons.toggle_on_outlined,
              title: 'Consent & Granular Controls',
              children: [
                'studentsyncsa uses a simple, transparent consent model. You are not asked to consent to data collection upfront — the app works entirely offline by default.',
                'Granular consent options will be introduced when cloud features (sync, backup) are added. At that point, you will be able to choose:',
                '• Essential: local-only storage required for the app to function',
                '• Sync & Backup: encrypt your data to the cloud for cross-device access',
                '• Analytics: anonymous usage data to help improve the app',
                '• Personalisation: tailored university and bursary recommendations',
                'Each option will default to off. You can change your choices at any time from Settings.',
              ],
            ),
            const SizedBox(height: 16),

            // Privacy-by-Design
            _Section(
              icon: Icons.architecture_outlined,
              title: 'Privacy-by-Design Principles',
              children: [
                'studentsyncsa is engineered with privacy as the default, not an afterthought.',
              ],
              trailing: Padding(
                padding: const EdgeInsets.only(top: 8),
                child: AppCard(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _PrincipleRow('On-device processing', 'All analytics, recommendations, and data processing happen inside the app. Raw data is never uploaded to servers.'),
                        _PrincipleRow('Data minimization', 'Only strictly necessary data is collected — enough to pre-fill forms and check eligibility. No data hoarding.'),
                        _PrincipleRow('No PII retained unnecessarily', 'Personal identifiers (ID numbers, names, contact details) are stored only as long as you keep them in the app. No external persistence.'),
                        _PrincipleRow('Explicit consent', 'Any tracking or data sharing requires your explicit opt-in. Consent dialogs state the purpose concisely before any action.'),
                        _PrincipleRow('Auto-discard', 'Session data and intermediate processing results are discarded when no longer needed. Non-identifiable state may persist for app functionality.'),
                        _PrincipleRow('Real-time processing', 'Recommendations and matches are computed in-memory at the moment you need them. Only the result is displayed; intermediate data is ephemeral.'),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Implementation Patterns
            _Section(
              icon: Icons.code_outlined,
              title: 'Implementation Patterns',
              children: [
                'How these principles are implemented in practice:',
              ],
              trailing: Padding(
                padding: const EdgeInsets.only(top: 8),
                child: AppCard(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _PrincipleRow('Local-only analytics', 'Feature usage and interaction signals are stored in a local Hive box or in-memory. Never synced to external servers.'),
                        _PrincipleRow('On-device recommender', 'The Star AI runs locally via Ollama. No prompts or responses leave your machine. University/bursary matching uses local data only.'),
                        _PrincipleRow('Ephemeral sessions', 'When you close the app, any temporary session state is purged. Only explicitly saved profile data persists.'),
                        _PrincipleRow('Clear exit path', 'Settings → Clear All Local Data removes all stored information permanently. Uninstalling the app achieves the same result.'),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Data Processing Agreements
            _Section(
              icon: Icons.article_outlined,
              title: 'Data Processing Agreements',
              children: [
                'studentsyncsa does not share your data with third-party processors. All data is stored locally on your device.',
                'When you submit an application to a university or bursary, data is sent directly to that institution\'s systems. Each institution acts as an independent data controller under POPIA.',
                'If future features introduce third-party services (e.g., cloud backup providers), we will publish Data Processing Agreements (DPAs) here and notify you before any data leaves your device.',
              ],
            ),
            const SizedBox(height: 16),

            // Records of Processing
            _Section(
              icon: Icons.list_alt_rounded,
              title: 'Records of Processing',
              children: [
                'We maintain a record of all data processed by the app. This record includes:',
              ],
              trailing: Padding(
                padding: const EdgeInsets.only(top: 8),
                child: AppCard(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _Bullet('Data category — personal info, academic records, application data, usage stats'),
                        _Bullet('Purpose — pre-fill forms, check eligibility, track applications, improve app'),
                        _Bullet('Lawful basis — user consent (POPIA Section 11), contractual necessity (application submissions)'),
                        _Bullet('Storage location — local device (Hive), never on external servers'),
                        _Bullet('Retention period — until user deletes (see Retention section)'),
                        _Bullet('Recipients — only the universities/bursaries you choose to apply to'),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Data Retention (detailed)
            _Section(
              icon: Icons.timer_outlined,
              title: 'Data Retention & Disposal',
              children: [
                'Your data is retained on your device for as long as you continue using the app. Specific retention periods by category:',
              ],
              trailing: Padding(
                padding: const EdgeInsets.only(top: 8),
                child: AppCard(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _RetentionRow('Profile info', 'Until deleted (Settings → Clear Data)'),
                        _RetentionRow('Academic records', 'Until deleted'),
                        _RetentionRow('Application drafts', 'Until submitted or deleted'),
                        _RetentionRow('Submitted applications', 'Until you delete or request removal'),
                        _RetentionRow('Document uploads', 'Until deleted'),
                        _RetentionRow('Usage analytics', 'Aggregated only, no personal data'),
                        const SizedBox(height: 8),
                        const Text(
                          'Disposal: when you clear data via Settings or uninstall the app, all stored information is permanently deleted. No residual copies are retained. For deletion requests, email privacy@studentsyncsa.app — we will confirm within 72 hours.',
                          style: TextStyle(fontSize: 12, color: AppColors.textMuted, height: 1.4),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Student Data & Consent
            _Section(
              icon: Icons.school_rounded,
              title: 'Student Data & Consent',
              children: [
                'studentsyncsa is designed for prospective university students. If you are under 18, please review this policy with a parent or guardian.',
                'By using the app, you consent to the collection and use of your information as described here. You may withdraw consent at any time by clearing your data and uninstalling the app.',
                'We do not sell, rent, or trade your personal information to third parties. Your data is used exclusively for the purpose of facilitating your educational applications.',
              ],
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  final IconData icon;
  final String title;
  final List<String> children;
  final Widget? trailing;

  const _Section({
    required this.icon,
    required this.title,
    required this.children,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: AppColors.primary, size: 20),
                const SizedBox(width: 10),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...children.map((text) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(
                text,
                style: const TextStyle(
                  fontSize: 13,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
              ),
            )),
            if (trailing != null) trailing!,
          ],
        ),
      ),
    );
  }
}

class _ContactLine extends StatelessWidget {
  final String label;
  final String value;
  const _ContactLine({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          SizedBox(
            width: 110,
            child: Text(label,
                style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textMuted)),
          ),
          Expanded(
            child: Text(value,
                style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }
}

class _Bullet extends StatelessWidget {
  final String text;
  const _Bullet(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('• ',
              style: TextStyle(
                  fontSize: 13,
                  color: AppColors.textMuted)),
          Expanded(
            child: Text(text,
                style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                    height: 1.4)),
          ),
        ],
      ),
    );
  }
}

class _RetentionRow extends StatelessWidget {
  final String category;
  final String period;
  const _RetentionRow(this.category, this.period);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(category,
                style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary)),
          ),
          Expanded(
            child: Text(period,
                style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textMuted)),
          ),
        ],
      ),
    );
  }
}

class _PrincipleRow extends StatelessWidget {
  final String title;
  final String description;
  const _PrincipleRow(this.title, this.description);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary)),
          const SizedBox(height: 2),
          Text(description,
              style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                  height: 1.4)),
        ],
      ),
    );
  }
}
