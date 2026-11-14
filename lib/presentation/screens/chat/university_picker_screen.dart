import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lipsyncstudent/core/theme/app_theme.dart';
import 'package:lipsyncstudent/domain/models/university.dart';
import 'package:lipsyncstudent/presentation/providers/university_provider.dart';
import 'package:lipsyncstudent/presentation/screens/chat/room_chat_screen.dart';

class UniversityPickerScreen extends ConsumerWidget {
  const UniversityPickerScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(universitiesProvider);
    return Container(
      color: Colors.black,
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          title: const Text('University Interest Groups'),
          centerTitle: true,
          backgroundColor: Colors.black,
          elevation: 0,
        ),
        body: async.when(
          loading: () => const Center(
            child: CircularProgressIndicator(color: AppColors.primary),
          ),
          error: (e, _) => Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                'Could not load universities: $e',
                style: const TextStyle(color: AppColors.error),
                textAlign: TextAlign.center,
              ),
            ),
          ),
          data: (universities) {
            if (universities.isEmpty) {
              return const Center(
                child: Text(
                  'No universities yet.',
                  style: TextStyle(color: AppColors.textMuted),
                ),
              );
            }
            final sorted = [...universities]
              ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
            return ListView.separated(
              padding: const EdgeInsets.all(12),
              itemCount: sorted.length,
              separatorBuilder: (_, _) => const SizedBox(height: 6),
              itemBuilder: (ctx, i) {
                final u = sorted[i];
                return _UniversityTile(
                  university: u,
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => RoomChatScreen(
                        room: 'university:${u.id}',
                        roomName: u.shortName.isNotEmpty ? u.shortName : u.name,
                      ),
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class _UniversityTile extends StatelessWidget {
  final University university;
  final VoidCallback onTap;
  const _UniversityTile({required this.university, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        splashColor: AppColors.primary.withValues(alpha: 0.15),
        highlightColor: AppColors.primary.withValues(alpha: 0.08),
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.primary, width: 1),
            color: Colors.black,
          ),
          child: Row(
            children: [
              Icon(Icons.school_rounded, color: AppColors.primary, size: 20),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      university.name,
                      style: const TextStyle(
                        color: AppColors.primary,
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (university.province.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        university.province,
                        style: const TextStyle(
                          color: AppColors.textMuted,
                          fontSize: 11,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: AppColors.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}
