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
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            AppCard(
              onTap: () => _showComingSoon(context),
              child: const ListTile(
                leading: Icon(Icons.chat_rounded, color: AppColors.primary),
                title: Text('General Chat',
                    style: TextStyle(color: AppColors.textPrimary)),
                subtitle: Text('Connect with students across SA',
                    style: TextStyle(color: AppColors.textSecondary)),
                trailing: Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted),
              ),
            ),
            const SizedBox(height: 8),
            AppCard(
              onTap: () => _showComingSoon(context),
              child: const ListTile(
                leading:
                    Icon(Icons.map_rounded, color: AppColors.success),
                title: Text('Province-based',
                    style: TextStyle(color: AppColors.textPrimary)),
                subtitle: Text('Chat with students from your province',
                    style: TextStyle(color: AppColors.textSecondary)),
                trailing: Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted),
              ),
            ),
            const SizedBox(height: 8),
            AppCard(
              onTap: () => _showComingSoon(context),
              child: const ListTile(
                leading:
                    Icon(Icons.school_rounded, color: AppColors.warning),
                title: Text('University Interest Groups',
                    style: TextStyle(color: AppColors.textPrimary)),
                subtitle: Text('Discuss with future classmates',
                    style: TextStyle(color: AppColors.textSecondary)),
                trailing: Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted),
              ),
            ),
          ],
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
            SizedBox(width: 8),
            Text('Coming Soon', style: TextStyle(color: AppColors.textPrimary)),
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
