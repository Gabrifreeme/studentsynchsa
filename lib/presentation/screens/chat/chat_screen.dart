import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class ChatScreen extends StatelessWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: const Text('Community Chat')),
        body: Center(
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width < 600
                  ? double.infinity
                  : MediaQuery.of(context).size.width * 0.5,
            ),
            child: ListView(
          padding: const EdgeInsets.all(11),
          children: [
            AppCard(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
              onTap: () => _showComingSoon(context),
              child: const SizedBox(
                height: 48,
                child: ListTile(
                dense: true,
                visualDensity: VisualDensity.compact,
                contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 0),
                minLeadingWidth: 22,
                leading: StarIcon(Icons.chat_rounded),
                title: Text('General Chat',
                    style: TextStyle(color: AppColors.textPrimary, fontSize: 11)),
                subtitle: Text('Discuss with future classmates',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 9)),
                trailing: Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted, size: 16),
                ),
              ),
            ),
            const SizedBox(height: 6),
            AppCard(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
              onTap: () => _showComingSoon(context),
              child: const SizedBox(
                height: 48,
                child: ListTile(
                dense: true,
                visualDensity: VisualDensity.compact,
                contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 0),
                minLeadingWidth: 22,
                leading:
                    StarIcon(Icons.map_rounded),
                title: Text('Province-based',
                    style: TextStyle(color: AppColors.textPrimary, fontSize: 11)),
                subtitle: Text('Chat with students from your province',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 9)),
                trailing: Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted, size: 16),
                ),
              ),
            ),
            const SizedBox(height: 6),
            AppCard(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
              onTap: () => _showComingSoon(context),
              child: const SizedBox(
                height: 48,
                child: ListTile(
                dense: true,
                visualDensity: VisualDensity.compact,
                contentPadding: EdgeInsets.symmetric(horizontal: 6, vertical: 0),
                minLeadingWidth: 22,
                leading:
                    StarIcon(Icons.school_rounded),
                title: Text('University Interest Groups',
                    style: TextStyle(color: AppColors.textPrimary, fontSize: 11)),
                subtitle: Text('Connect with students across South Africa',
                    style: TextStyle(color: AppColors.textSecondary, fontSize: 9)),
                trailing: Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted, size: 16),
                ),
              ),
            ),
          ],
        ),
          ),
        ),
      ),
    );
  }

  void _showComingSoon(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Row(
          children: [
            StarAvatar(size: 24),
            SizedBox(width: 6),
            Text('Coming Soon', style: TextStyle(color: AppColors.textPrimary, fontSize: 11)),
          ],
        ),
        content: const Text(
          'Community chat is coming in the next update! Star is working on it.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Okay'),
          ),
        ],
      ),
    );
  }
}
