import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/repositories/application_repository_impl.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/application.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/domain/models/university.dart';
import 'package:studentsyncsa/domain/repositories/application_repository.dart';

class ApplicationFormScreen extends StatefulWidget {
  final University university;
  const ApplicationFormScreen({super.key, required this.university});

  @override
  State<ApplicationFormScreen> createState() => _ApplicationFormScreenState();
}

class _ApplicationFormScreenState extends State<ApplicationFormScreen> {
  final _repo = ApplicationRepositoryImpl();
  StudentProfile? _profile;
  bool _loading = true;
  bool _agreed = false;
  bool _submitting = false;

  String? _selectedFaculty;
  String _studyMode = 'Full-Time';
  final _courseCtrl = TextEditingController();

  final _studyModes = ['Full-Time', 'Part-Time', 'Distance Learning'];

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final repo = ProfileRepositoryImpl();
    var p = await repo.getProfile();
    if (p == null) {
      await Future.delayed(const Duration(seconds: 1));
      p = await repo.getProfile();
    }
    if (mounted) setState(() { _profile = p; _loading = false; });
  }

  @override
  void dispose() {
    _courseCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final uni = widget.university;

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text('Apply — ${uni.shortName}')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final profile = _profile;
    if (profile == null) {
      return Scaffold(
        appBar: AppBar(title: Text('Apply — ${uni.shortName}')),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text('No profile found. Complete your profile first, then come back.',
                textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text('✨ Apply — ${uni.shortName}')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _sectionHeader('University', Icons.school),
            _readOnlyRow('University', uni.name),
            _readOnlyRow('Faculty', uni.faculties.isNotEmpty ? (uni.faculties.length > 1 ? 'Select below' : uni.faculties.first) : '—'),

            const SizedBox(height: 20),
            _sectionHeader('Personal', Icons.person),
            _readOnlyRow('Name', '${profile.personal.title} ${profile.personal.firstName} ${profile.personal.lastName}'),
            if (profile.personal.gender.isNotEmpty) _readOnlyRow('Gender', profile.personal.gender),
            if (profile.personal.dateOfBirth != null) _readOnlyRow('Date of Birth', profile.personal.dateOfBirth!.toIso8601String().split('T').first),
            if (profile.personal.idNumber.isNotEmpty) _readOnlyRow('ID Number', profile.personal.idNumber),

            const SizedBox(height: 20),
            _sectionHeader('Contact', Icons.contact_mail),
            if (profile.contact.email.isNotEmpty) _readOnlyRow('Email', profile.contact.email),
            if (profile.contact.phone.isNotEmpty) _readOnlyRow('Phone', profile.contact.phone),

            const SizedBox(height: 20),
            _sectionHeader('Address', Icons.location_on),
            if (profile.address.address.isNotEmpty) _readOnlyRow('Address', profile.address.address),
            if (profile.address.province.isNotEmpty) _readOnlyRow('Province', profile.address.province),
            if (profile.address.postalCode.isNotEmpty) _readOnlyRow('Postal Code', profile.address.postalCode),

            const SizedBox(height: 20),
            _sectionHeader('School', Icons.school_outlined),
            if (profile.school.schoolName.isNotEmpty) _readOnlyRow('School', profile.school.schoolName),
            if (profile.school.currentGrade.isNotEmpty) _readOnlyRow('Current Grade', profile.school.currentGrade),

            if (profile.results.subjects.isNotEmpty) ...[
              const SizedBox(height: 20),
              _sectionHeader('Subjects & Results', Icons.assignment),
              ...profile.results.subjects.map((s) =>
                Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    children: [
                      Expanded(flex: 3, child: Text(s.subject, style: const TextStyle(fontSize: 13, color: AppColors.textPrimary))),
                      Expanded(flex: 1, child: Text(s.grade, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))),
                      SizedBox(width: 60, child: Text('${s.result} ${s.symbol}', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))),
                    ],
                  ),
                ),
              ),
            ],

            const SizedBox(height: 20),
            _sectionHeader('Your Choices', Icons.edit),
            const SizedBox(height: 8),
            InkWell(
              onTap: () => _showFacultyPicker(uni.faculties),
              borderRadius: BorderRadius.circular(12),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLight,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        _selectedFaculty ?? 'Select Faculty',
                        style: TextStyle(
                          color: _selectedFaculty != null ? AppColors.textPrimary : AppColors.textMuted,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    const Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: () => _showCoursePicker(profile),
              borderRadius: BorderRadius.circular(12),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLight,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        _courseCtrl.text.isEmpty ? 'Course / Programme' : _courseCtrl.text,
                        style: TextStyle(
                          color: _courseCtrl.text.isNotEmpty ? AppColors.textPrimary : AppColors.textMuted,
                          fontSize: 14,
                        ),
                      ),
                    ),
                    const Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _studyMode,
              decoration: _inputDecoration('Study Mode'),
              dropdownColor: AppColors.card,
              style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
              items: _studyModes.map((m) => DropdownMenuItem(value: m, child: Text(m, style: const TextStyle(fontSize: 13)))).toList(),
              onChanged: (v) => setState(() => _studyMode = v ?? 'Full-Time'),
            ),

            const SizedBox(height: 20),
            _sectionHeader('Declaration', Icons.check_circle_outline),
            const SizedBox(height: 8),
            CheckboxListTile(
              value: _agreed,
              onChanged: (v) => setState(() => _agreed = v ?? false),
              title: const Text('I confirm that all the information above is correct to the best of my knowledge.',
                  style: TextStyle(fontSize: 13, color: AppColors.textSecondary)),
              activeColor: AppColors.primary,
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
            ),

            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _agreed && !_submitting ? _submit : null,
                icon: _submitting
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.send_rounded, size: 20),
                label: Text(_submitting ? 'Submitting...' : '✨ Submit Application'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  backgroundColor: AppColors.primary,
                  disabledBackgroundColor: AppColors.surfaceLight,
                ),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  InputDecoration _inputDecoration(String hint) => InputDecoration(
    hintText: hint,
    hintStyle: const TextStyle(color: AppColors.textMuted, fontSize: 14),
    filled: true,
    fillColor: AppColors.surfaceLight,
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
  );

  void _showFacultyPicker(List<String> faculties) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const SizedBox(height: 12),
          Container(width: 40, height: 4, decoration: BoxDecoration(color: AppColors.textMuted, borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 16),
          const Text('Select Faculty', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
          const SizedBox(height: 12),
          ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 400),
            child: ListView(
              shrinkWrap: true,
              children: faculties.map((f) => ListTile(
                title: Text(f, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
                trailing: _selectedFaculty == f ? const Icon(Icons.check, color: AppColors.primary, size: 20) : null,
                onTap: () {
                  setState(() => _selectedFaculty = f);
                  Navigator.pop(ctx);
                },
              )).toList(),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  void _showCoursePicker(StudentProfile profile) {
    final choices = profile.qualification.choices;
    var courses = choices.map((c) => c.programme).where((p) => p.isNotEmpty).toList();
    if (_selectedFaculty != null) {
      final matching = choices.where((c) => c.faculty == _selectedFaculty).map((c) => c.programme).where((p) => p.isNotEmpty).toList();
      if (matching.isNotEmpty) courses = matching;
    }
    courses = courses.toSet().toList()..sort();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        final searchCtrl = TextEditingController();
        return StatefulBuilder(
          builder: (ctx, setDialogState) {
            final q = searchCtrl.text.toLowerCase();
            final filtered = courses.where((c) => q.isEmpty || c.toLowerCase().contains(q)).toList();
            return DraggableScrollableSheet(
              initialChildSize: 0.7,
              maxChildSize: 0.9,
              minChildSize: 0.5,
              expand: false,
              builder: (ctx, scrollCtrl) => Column(
                children: [
                  const SizedBox(height: 12),
                  Container(width: 40, height: 4, decoration: BoxDecoration(color: AppColors.textMuted, borderRadius: BorderRadius.circular(2))),
                  const SizedBox(height: 16),
                  const Text('Select Course / Programme', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
                  const SizedBox(height: 12),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: TextField(
                      controller: searchCtrl,
                      autofocus: true,
                      decoration: InputDecoration(
                        hintText: 'Search courses...',
                        prefixIcon: const Icon(Icons.search, color: AppColors.textMuted),
                        suffixIcon: searchCtrl.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear, size: 18),
                                onPressed: () { searchCtrl.clear(); setDialogState(() {}); },
                              )
                            : null,
                      ),
                      onChanged: (_) => setDialogState(() {}),
                    ),
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: filtered.isEmpty
                        ? const Center(child: Text('No matching courses', style: TextStyle(color: AppColors.textMuted)))
                        : ListView.builder(
                            controller: scrollCtrl,
                            itemCount: filtered.length,
                            itemBuilder: (ctx, i) => ListTile(
                              title: Text(filtered[i], style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
                              trailing: _courseCtrl.text == filtered[i] ? const Icon(Icons.check, color: AppColors.primary, size: 20) : null,
                              onTap: () {
                                _courseCtrl.text = filtered[i];
                                setState(() {});
                                Navigator.pop(ctx);
                              },
                            ),
                          ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void _submit() async {
    setState(() => _submitting = true);
    try {
      final app = UniversityApplication(
        id: const Uuid().v4(),
        universityId: widget.university.id,
        universityName: widget.university.shortName,
        course: _courseCtrl.text,
        faculty: _selectedFaculty ?? '',
        status: ApplicationStatus.submitted,
      );
      await _repo.saveApplication(app);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✅ Application to ${widget.university.shortName} submitted!'),
          backgroundColor: AppColors.success,
        ),
      );
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed: $e'), backgroundColor: AppColors.error),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Widget _sectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 16, color: AppColors.primaryLight),
        const SizedBox(width: 8),
        Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
      ],
    );
  }

  Widget _readOnlyRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 100, child: Text(label, style: const TextStyle(fontSize: 12, color: AppColors.textMuted))),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 13, color: AppColors.textPrimary))),
        ],
      ),
    );
  }
}
