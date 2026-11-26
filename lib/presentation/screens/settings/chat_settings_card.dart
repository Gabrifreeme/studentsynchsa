import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:studentsyncsa/core/constants/app_constants.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/services/chat_service.dart';

/// Enter the Supabase project URL + anon key here. Leave blank for device-local chat.
class ChatSettingsCard extends StatefulWidget {
  const ChatSettingsCard({super.key});

  @override
  State<ChatSettingsCard> createState() => _ChatSettingsCardState();
}

class _ChatSettingsCardState extends State<ChatSettingsCard> {
  final _url = TextEditingController();
  final _key = TextEditingController();
  final _name = TextEditingController();

  @override
  void initState() {
    super.initState();
    final box = Hive.box<String>(AppConstants.settingsBox);
    _url.text = box.get('supabaseUrl') ?? '';
    _key.text = box.get('supabaseAnonKey') ?? '';
    _name.text = box.get('chatUserName') ?? 'Student';
  }

  @override
  void dispose() {
    _url.dispose();
    _key.dispose();
    _name.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const StarIcon(Icons.forum_outlined, size: 16),
                const SizedBox(width: 6),
                const Text(
                  'Community Chat backend (Supabase)',
                  style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 11,
                      fontWeight: FontWeight.w700),
                ),
                const Spacer(),
                Text(
                  ChatService.isConfigured ? 'LIVE' : 'Local only',
                  style: TextStyle(
                      color:
                          ChatService.isConfigured ? AppColors.success : AppColors.textMuted,
                      fontSize: 9),
                ),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _url,
              style: const TextStyle(color: AppColors.textPrimary, fontSize: 11),
              decoration: const InputDecoration(
                  labelText: 'Project URL',
                  hintText: 'https://xxxx.supabase.co',
                  labelStyle: TextStyle(color: AppColors.textSecondary),
                  hintStyle: TextStyle(color: AppColors.textMuted, fontSize: 10)),
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _key,
              obscureText: true,
              style: const TextStyle(color: AppColors.textPrimary, fontSize: 11),
              decoration: const InputDecoration(
                  labelText: 'Anon / publishable key',
                  labelStyle: TextStyle(color: AppColors.textSecondary)),
            ),
            const SizedBox(height: 6),
            TextField(
              controller: _name,
              style: const TextStyle(color: AppColors.textPrimary, fontSize: 11),
              decoration: const InputDecoration(
                  labelText: 'Your display name',
                  hintText: 'Student',
                  labelStyle: TextStyle(color: AppColors.textSecondary),
                  hintStyle: TextStyle(color: AppColors.textMuted, fontSize: 10)),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: OutlinedButton.icon(
                onPressed: () async {
                  await ChatService.configure(_url.text, _key.text);
                  await Hive.box<String>(AppConstants.settingsBox)
                      .put('chatUserName', _name.text.trim().isEmpty
                          ? 'Student'
                          : _name.text.trim());
                  if (!mounted) return;
                  setState(() {});
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Chat settings saved'),
                      backgroundColor: AppColors.success,
                    ),
                  );
                },
                icon: const StarIcon(Icons.check_rounded, size: 14),
                label: const Text('Save'),
                style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: AppColors.primary),
                    foregroundColor: AppColors.primary,
                    textStyle: const TextStyle(fontSize: 11)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
