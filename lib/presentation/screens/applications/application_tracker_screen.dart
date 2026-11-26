import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/domain/models/application.dart';
import 'package:studentsyncsa/presentation/providers/application_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class ApplicationTrackerScreen extends ConsumerStatefulWidget {
  const ApplicationTrackerScreen({super.key});

  @override
  ConsumerState<ApplicationTrackerScreen> createState() =>
      _ApplicationTrackerScreenState();
}

class _ApplicationTrackerScreenState
    extends ConsumerState<ApplicationTrackerScreen> {
  @override
  Widget build(BuildContext context) {
    final appsAsync = ref.watch(applicationsProvider);

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('Your Progress'),
        ),
        body: appsAsync.when(
          data: (apps) {
            if (apps.isEmpty) return const SizedBox.shrink();
            return RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(applicationsProvider);
                await Future.delayed(const Duration(milliseconds: 300));
              },
              child: ListView.builder(
                padding: const EdgeInsets.all(11),
                itemCount: apps.length,
                itemBuilder: (_, i) => _buildAppCard(apps[i]),
              ),
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => EmptyState(
            icon: Icons.error_outline,
            title: 'Error loading applications',
            subtitle: e.toString(),
          ),
        ),
      ),
    );
  }

  Widget _buildAppCard(UniversityApplication app) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(app.universityName,
                      style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.bold,
                          fontSize: 10)),
                ),
                _StatusChip(app.status),
              ],
            ),
            if (app.course.isNotEmpty) ...[
              const SizedBox(height: 3),
              Text(app.course,
                  style: const TextStyle(
                      color: AppColors.textSecondary, fontSize: 9)),
            ],
            const SizedBox(height: 6),
            Row(
              children: [
                _InfoChip(Icons.monetization_on_outlined,
                    app.feePaid ? 'Fee Paid' : 'Fee Not Paid',
                    app.feePaid),
                const SizedBox(width: 6),
                _InfoChip(Icons.assignment_outlined,
                    app.nbtCompleted ? 'NBT Done' : 'NBT Pending',
                    app.nbtCompleted),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                IconButton(
                  icon: const Icon(Icons.edit_outlined, size: 18),
                  color: AppColors.textMuted,
                  onPressed: () => _showEditDialog(app),
                ),
                IconButton(
                  icon: const Icon(Icons.delete_outlined, size: 18),
                  color: AppColors.error,
                  onPressed: () => ref
                      .read(applicationsProvider.notifier)
                      .delete(app.id),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showEditDialog(UniversityApplication app) {
    final uniCtrl = TextEditingController(text: app.universityName);
    final courseCtrl = TextEditingController(text: app.course);
    final formKey = GlobalKey<FormState>();
    var status = app.status;
    var feePaid = app.feePaid;
    var nbtDone = app.nbtCompleted;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          backgroundColor: AppColors.surface,
          title: const Text('Edit Application',
              style: TextStyle(color: AppColors.textPrimary)),
          content: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextFormField(
                    controller: uniCtrl,
                    decoration:
                        const InputDecoration(labelText: 'University Name'),
                  ),
                  const SizedBox(height: 8),
                  TextFormField(
                    controller: courseCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Course / Programme'),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<ApplicationStatus>(
                    initialValue: status,
                    decoration: const InputDecoration(labelText: 'Status'),
                    items: ApplicationStatus.values
                        .map((s) => DropdownMenuItem(
                            value: s, child: Text(s.label)))
                        .toList(),
                    onChanged: (v) =>
                        setDialogState(() => status = v ?? status),
                  ),
                  const SizedBox(height: 8),
                  CheckboxListTile(
                    title: const Text('Application Fee Paid'),
                    value: feePaid,
                    onChanged: (v) => setDialogState(() => feePaid = v ?? false),
                    controlAffinity: ListTileControlAffinity.leading,
                  ),
                  CheckboxListTile(
                    title: const Text('NBT Completed'),
                    value: nbtDone,
                    onChanged: (v) => setDialogState(() => nbtDone = v ?? false),
                    controlAffinity: ListTileControlAffinity.leading,
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                final updated = app.copyWith(
                  universityName: uniCtrl.text.trim(),
                  course: courseCtrl.text.trim(),
                  status: status,
                  feePaid: feePaid,
                  nbtCompleted: nbtDone,
                );
                ref.read(applicationsProvider.notifier).update(updated);
                Navigator.pop(ctx);
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final ApplicationStatus status;
  const _StatusChip(this.status);

  @override
  Widget build(BuildContext context) {
    Color color;
    switch (status) {
      case ApplicationStatus.accepted:
        color = AppColors.success;
        break;
      case ApplicationStatus.rejected:
        color = AppColors.error;
        break;
      case ApplicationStatus.submitted:
      case ApplicationStatus.waitingResponse:
        color = AppColors.warning;
        break;
      default:
        color = AppColors.textMuted;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(status.label,
          style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool active;
  const _InfoChip(this.icon, this.label, this.active);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
      decoration: BoxDecoration(
        color: (active ? AppColors.success : AppColors.textMuted)
            .withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon,
              size: 12,
              color: active ? AppColors.success : AppColors.textMuted),
          const SizedBox(width: 3),
          Text(label,
              style: TextStyle(
                  color: active ? AppColors.success : AppColors.textMuted,
                  fontSize: 10)),
        ],
      ),
    );
  }
}
