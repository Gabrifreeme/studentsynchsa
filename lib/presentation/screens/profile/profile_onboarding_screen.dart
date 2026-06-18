import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';
import 'package:studentsynchsa/core/constants/app_constants.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/domain/models/student_profile.dart';
import 'package:studentsynchsa/presentation/providers/auth_provider.dart';
import 'package:studentsynchsa/presentation/providers/profile_provider.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';

class ProfileOnboardingScreen extends ConsumerStatefulWidget {
  const ProfileOnboardingScreen({super.key});

  @override
  ConsumerState<ProfileOnboardingScreen> createState() =>
      _ProfileOnboardingScreenState();
}

class _ProfileOnboardingScreenState
    extends ConsumerState<ProfileOnboardingScreen> {
  final _pageController = PageController();
  int _currentPage = 0;

  // Controllers
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _idCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _addressCtrl = TextEditingController();
  final _schoolCtrl = TextEditingController();

  String _gender = '';
  String _nationality = 'South African';
  String _province = '';
  String _grade = '';
  List<SubjectMark> _subjects = [];
  List<String> _careerInterests = [];
  bool _saving = false;

  final _formKeys = List.generate(4, (_) => GlobalKey<FormState>());

  @override
  void dispose() {
    _pageController.dispose();
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _idCtrl.dispose();
    _phoneCtrl.dispose();
    _addressCtrl.dispose();
    _schoolCtrl.dispose();
    super.dispose();
  }

  bool _validateCurrentPage() {
    return _formKeys[_currentPage].currentState?.validate() ?? false;
  }

  Future<void> _saveAndContinue() async {
    if (!_validateCurrentPage()) return;
    if (_currentPage < 3) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      await _saveProfile();
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _saving = true);
    final authState = ref.read(authProvider);
    final existingProfile = authState.value?.profile;
    final id = existingProfile?.id ?? const Uuid().v4();
    final email = existingProfile?.email ?? '';

    final profile = StudentProfile(
      id: id,
      email: email,
      firstName: _firstNameCtrl.text.trim(),
      lastName: _lastNameCtrl.text.trim(),
      idNumber: _idCtrl.text.trim(),
      phone: _phoneCtrl.text.trim(),
      address: _addressCtrl.text.trim(),
      province: _province,
      schoolName: _schoolCtrl.text.trim(),
      currentGrade: _grade,
      gender: _gender,
      nationality: _nationality,
      grade12Subjects: _subjects,
      careerInterests: _careerInterests,
      onboardingComplete: true,
    );

    await ref.read(profileProvider.notifier).saveProfile(profile);
    ref.read(authProvider.notifier).completeOnboarding(profile);
    setState(() => _saving = false);
    if (mounted) context.go('/dashboard');
  }

  Widget _buildProgressBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        children: List.generate(4, (i) {
          return Expanded(
            child: Container(
              height: 4,
              margin: const EdgeInsets.symmetric(horizontal: 2),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(2),
                color: i <= _currentPage
                    ? AppColors.primary
                    : AppColors.surfaceLight,
              ),
            ),
          );
        }),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('Complete Your Profile'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios),
            onPressed: _currentPage > 0
                ? () => _pageController.previousPage(
                      duration: const Duration(milliseconds: 300),
                      curve: Curves.easeInOut,
                    )
                : () => context.pop(),
          ),
        ),
        body: Column(
          children: [
            _buildProgressBar(),
            Text(
              'Step ${_currentPage + 1} of 4',
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: PageView(
                controller: _pageController,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (i) => setState(() => _currentPage = i),
                children: [
                  _buildPersonalInfo(),
                  _buildSchoolInfo(),
                  _buildSubjectsPage(),
                  _buildPreferencesPage(),
                ],
              ),
            ),
            _buildBottomButtons(),
          ],
        ),
      ),
    );
  }

  Widget _buildPersonalInfo() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[0],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Personal Information',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text("Let's start with the basics",
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _firstNameCtrl,
                    decoration: const InputDecoration(
                        labelText: 'First Name',
                        prefixIcon: Icon(Icons.person_outline)),
                    validator: (v) =>
                        v?.isEmpty == true ? 'Required' : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _lastNameCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Last Name',
                        prefixIcon: Icon(Icons.person_outline)),
                    validator: (v) =>
                        v?.isEmpty == true ? 'Required' : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _idCtrl,
              decoration: const InputDecoration(
                labelText: 'ID / Passport Number',
                prefixIcon: Icon(Icons.badge_outlined),
              ),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _gender.isEmpty ? null : _gender,
              decoration: const InputDecoration(
                labelText: 'Gender',
                prefixIcon: Icon(Icons.wc_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Male', child: Text('Male')),
                DropdownMenuItem(value: 'Female', child: Text('Female')),
                DropdownMenuItem(value: 'Other', child: Text('Other')),
                DropdownMenuItem(
                    value: 'Prefer not to say',
                    child: Text('Prefer not to say')),
              ],
              onChanged: (v) => setState(() => _gender = v ?? ''),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _nationality,
              decoration: const InputDecoration(
                labelText: 'Nationality',
                prefixIcon: Icon(Icons.flag_outlined),
              ),
              items: const [
                DropdownMenuItem(
                    value: 'South African', child: Text('South African')),
                DropdownMenuItem(
                    value: 'Other African', child: Text('Other African')),
                DropdownMenuItem(
                    value: 'International', child: Text('International')),
              ],
              onChanged: (v) => setState(() => _nationality = v ?? 'South African'),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _phoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Phone Number',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _addressCtrl,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: 'Home Address',
                prefixIcon: Icon(Icons.home_outlined),
              ),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _province.isEmpty ? null : _province,
              decoration: const InputDecoration(
                labelText: 'Province',
                prefixIcon: Icon(Icons.map_outlined),
              ),
              items: AppConstants.provinces
                  .map((p) => DropdownMenuItem(value: p, child: Text(p)))
                  .toList(),
              onChanged: (v) => setState(() => _province = v ?? ''),
              validator: (v) => v == null ? 'Select your province' : null,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSchoolInfo() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[1],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('School Information',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Where and what are you studying?',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            TextFormField(
              controller: _schoolCtrl,
              decoration: const InputDecoration(
                labelText: 'School Name',
                prefixIcon: Icon(Icons.school_outlined),
              ),
              validator: (v) => v?.isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _grade.isEmpty ? null : _grade,
              decoration: const InputDecoration(
                labelText: 'Current / Completed Grade',
                prefixIcon: Icon(Icons.grade_outlined),
              ),
              items: AppConstants.grades
                  .map((g) => DropdownMenuItem(value: g, child: Text(g)))
                  .toList(),
              onChanged: (v) => setState(() => _grade = v ?? ''),
              validator: (v) => v == null ? 'Select your grade' : null,
            ),
            const SizedBox(height: 24),
            const Text('Subjects & Marks (Grade 12)',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            const Text('Add at least 6 subjects for APS calculation',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
            const SizedBox(height: 12),
            ..._subjects.asMap().entries.map((entry) {
              final i = entry.key;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    Expanded(
                      flex: 3,
                      child: DropdownButtonFormField<String>(
                        value: _subjects[i].subject.isEmpty
                            ? null
                            : _subjects[i].subject,
                        decoration: const InputDecoration(
                          labelText: 'Subject',
                          contentPadding:
                              EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        ),
                        items: AppConstants.subjects
                            .map((s) =>
                                DropdownMenuItem(value: s, child: Text(s, style: const TextStyle(fontSize: 13))))
                            .toList(),
                        onChanged: (v) {
                          if (v != null) {
                            setState(() => _subjects[i] = _subjects[i].copyWith(subject: v));
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      flex: 1,
                      child: TextFormField(
                        initialValue: _subjects[i].mark == 0
                            ? ''
                            : _subjects[i].mark.toInt().toString(),
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: '%',
                          contentPadding:
                              EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                        ),
                        onChanged: (v) {
                          final mark = double.tryParse(v) ?? 0;
                          setState(
                              () => _subjects[i] = _subjects[i].copyWith(mark: mark));
                        },
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.remove_circle_outline,
                          color: AppColors.error, size: 20),
                      onPressed: () =>
                          setState(() => _subjects.removeAt(i)),
                    ),
                  ],
                ),
              );
            }),
            OutlinedButton.icon(
              onPressed: () {
                setState(() => _subjects.add(const SubjectMark(subject: '', mark: 0)));
              },
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Add Subject'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.primaryLight,
                side: const BorderSide(color: AppColors.border),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubjectsPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[2],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Additional Subjects',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Add Grade 11 subjects if you have them',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            const Text('Your APS Score',
                style: TextStyle(
                    color: AppColors.primary,
                    fontSize: 32,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            OutlinedButton(
              onPressed: () => context.push('/aps-calculator'),
              child: const Text('Open APS Calculator'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPreferencesPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[3],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Your Preferences',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text("What are you interested in?",
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            const Text('Career Interests',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: AppConstants.careerInterests.map((interest) {
                final selected = _careerInterests.contains(interest);
                return FilterChip(
                  label: Text(interest, style: const TextStyle(fontSize: 12)),
                  selected: selected,
                  onSelected: (v) {
                    setState(() {
                      if (v) {
                        _careerInterests.add(interest);
                      } else {
                        _careerInterests.remove(interest);
                      }
                    });
                  },
                  selectedColor: AppColors.primary.withValues(alpha: 0.3),
                  checkmarkColor: AppColors.primaryLight,
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomButtons() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          if (_currentPage > 0)
            Expanded(
              child: OutlinedButton(
                onPressed: () => _pageController.previousPage(
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeInOut,
                ),
                child: const Text('Back'),
              ),
            ),
          if (_currentPage > 0) const SizedBox(width: 12),
          Expanded(
            child: ElevatedButton(
              onPressed: _saving ? null : _saveAndContinue,
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : Text(_currentPage < 3 ? 'Continue' : 'Finish'),
            ),
          ),
        ],
      ),
    );
  }
}
