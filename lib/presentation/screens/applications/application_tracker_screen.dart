import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';
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
          title: const Text('My Applications'),
          actions: [
            IconButton(
              icon: const Icon(Icons.add_rounded),
              onPressed: () => _showAddDialog(),
            ),
          ],
        ),
        body: appsAsync.when(
          data: (apps) {
            if (apps.isEmpty) {
              return const EmptyState(
                icon: Icons.assignment_outlined,
                title: 'No applications yet',
                subtitle: 'Tap + to add your first university application',
              );
            }
            return RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(applicationsProvider);
                // Wait for provider to reload
                await Future.delayed(const Duration(milliseconds: 300));
              },
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
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
                          fontSize: 15)),
                ),
                _StatusChip(app.status),
              ],
            ),
            if (app.course.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(app.course,
                  style: const TextStyle(
                      color: AppColors.textSecondary, fontSize: 13)),
            ],
            const SizedBox(height: 8),
            Row(
              children: [
                _InfoChip(Icons.monetization_on_outlined,
                    app.feePaid ? 'Fee Paid' : 'Fee Not Paid',
                    app.feePaid),
                const SizedBox(width: 8),
                _InfoChip(Icons.assignment_outlined,
                    app.nbtCompleted ? 'NBT Done' : 'NBT Pending',
                    app.nbtCompleted),
              ],
            ),
            const SizedBox(height: 8),
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

  void _showAddDialog() {
    final uniCtrl = TextEditingController();
    final courseCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('New Application',
            style: TextStyle(color: AppColors.textPrimary)),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: uniCtrl,
                decoration: const InputDecoration(labelText: 'University Name'),
                validator: (v) => v?.isEmpty == true ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: courseCtrl,
                decoration: const InputDecoration(labelText: 'Course / Programme'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                final app = UniversityApplication(
                  id: const Uuid().v4(),
                  universityId: uniCtrl.text.trim(),
                  universityName: uniCtrl.text.trim(),
                  course: courseCtrl.text.trim(),
                );
                ref.read(applicationsProvider.notifier).save(app);
                Navigator.pop(ctx);
              }
            },
            child: const Text('Add'),
          ),
        ],
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
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: courseCtrl,
                    decoration:
                        const InputDecoration(labelText: 'Course / Programme'),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<ApplicationStatus>(
                    value: status,
                    decoration: const InputDecoration(labelText: 'Status'),
                    items: ApplicationStatus.values
                        .map((s) => DropdownMenuItem(
                            value: s, child: Text(s.label)))
                        .toList(),
                    onChanged: (v) =>
                        setDialogState(() => status = v ?? status),
                  ),
                  const SizedBox(height: 12),
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(8),
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: (active ? AppColors.success : AppColors.textMuted)
            .withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon,
              size: 12,
              color: active ? AppColors.success : AppColors.textMuted),
          const SizedBox(width: 4),
          Text(label,
              style: TextStyle(
                  color: active ? AppColors.success : AppColors.textMuted,
                  fontSize: 10)),
        ],
      ),
    );
  }
}
