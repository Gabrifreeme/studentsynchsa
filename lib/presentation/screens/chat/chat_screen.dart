import 'package:flutter/material.dart';
import 'package:lipsyncstudent/core/theme/app_theme.dart';
import 'package:lipsyncstudent/presentation/screens/chat/room_chat_screen.dart';
import 'package:lipsyncstudent/presentation/screens/chat/university_picker_screen.dart';
import 'package:lipsyncstudent/presentation/widgets/common_widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lipsyncstudent/presentation/providers/profile_provider.dart';

class ChatScreen extends ConsumerWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      color: Colors.black,
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(title: const Text('Community Chat')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            AppCard(
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const RoomChatScreen(room: 'general', roomName: 'General Chat'))),
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
              onTap: () {
                final profile = ref.read(profileProvider).valueOrNull;
                final raw = profile?.address.province.trim() ?? '';
                if (raw.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Set your province in Profile first'),
                      backgroundColor: AppColors.error,
                    ),
                  );
                  return;
                }
                final slug = _slugifyProvince(raw);
                Navigator.push(context, MaterialPageRoute(builder: (_) => RoomChatScreen(
                  room: 'province:$slug',
                  roomName: raw,
                )));
              },
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
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const UniversityPickerScreen())),
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

  static String _slugifyProvince(String raw) {
    final lower = raw.toLowerCase();
    final re = RegExp(r'[^a-z0-9]+');
    final dashed = lower.replaceAll(re, '-');
    return dashed.replaceAll(RegExp(r'^-+|-+$'), '');
  }
}
