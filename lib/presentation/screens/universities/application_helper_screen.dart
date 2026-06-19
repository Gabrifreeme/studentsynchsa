import 'package:flutter/services.dart';
import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';

class ApplicationHelperScreen extends StatefulWidget {
  final String universityName;
  const ApplicationHelperScreen({super.key, required this.universityName});

  @override
  State<ApplicationHelperScreen> createState() => _ApplicationHelperScreenState();
}

class _ApplicationHelperScreenState extends State<ApplicationHelperScreen> {
  StudentProfile? _profile;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final repo = ProfileRepositoryImpl();
    var p = await repo.getProfile();
    if (p == null) {
      await Future.delayed(const Duration(seconds: 1));
      p = await repo.getProfile();
    }
    if (mounted) setState(() { _profile = p; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Application Helper')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final profile = _profile;
    if (profile == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Application Helper')),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text('No profile found. Go to My Profile and complete your details first.\n\nThen come back here.',
                textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
          ),
        ),
      );
    }
    return Scaffold(
      appBar: AppBar(title: Text('${widget.universityName} — Copy & Paste')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Tap a field to copy it, then paste into the university form.',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
            const SizedBox(height: 8),
            if (profile.onboardingComplete)
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.check_circle, size: 14, color: AppColors.success),
                    SizedBox(width: 6),
                    Text('Profile complete', style: TextStyle(fontSize: 11, color: AppColors.success)),
                  ],
                ),
              ),
            const SizedBox(height: 16),
            _section('Personal', [
              _field(context, profile.personal.title, 'Title'),
              _field(context, profile.personal.firstName, 'First Name'),
              _field(context, profile.personal.lastName, 'Last Name'),
              _field(context, profile.personal.gender, 'Gender'),
              _field(context, profile.personal.dateOfBirth?.toIso8601String().split('T').first ?? '', 'Date of Birth'),
              _field(context, profile.personal.idNumber, 'ID Number'),
            ]),
            _section('Contact', [
              _field(context, profile.contact.email, 'Email'),
              _field(context, profile.contact.phone, 'Phone'),
              _field(context, profile.contact.workPhone, 'Work Phone'),
            ]),
            _section('Address', [
              _field(context, profile.address.address, 'Address'),
              _field(context, profile.address.addressLine2, 'Address Line 2'),
              _field(context, profile.address.province, 'Province'),
              _field(context, profile.address.postalCode, 'Postal Code'),
            ]),
            _section('Demographic', [
              _field(context, profile.demographic.nationality, 'Nationality'),
              _field(context, profile.demographic.countryOfBirth, 'Country of Birth'),
              _field(context, profile.demographic.homeLanguage, 'Home Language'),
              _field(context, profile.demographic.populationGroup, 'Population Group'),
              _field(context, profile.demographic.maritalStatus, 'Marital Status'),
            ]),
            _section('School', [
              _field(context, profile.school.schoolName, 'School Name'),
              _field(context, profile.school.currentGrade, 'Grade'),
              _field(context, profile.school.currentlyDoing, 'Currently Doing'),
            ]),
            _section('Next of Kin', [
              _field(context, profile.nextOfKin.name, 'Name'),
              _field(context, profile.nextOfKin.mobilePhone, 'Mobile'),
              _field(context, profile.nextOfKin.homePhone, 'Home Phone'),
              _field(context, profile.nextOfKin.email, 'Email'),
              _field(context, '${profile.nextOfKin.addressLine1}, ${profile.nextOfKin.addressLine2}', 'Address'),
              _field(context, profile.nextOfKin.postalCode, 'Postal Code'),
            ]),
            _section('Account Contact', [
              _field(context, profile.accountContact.name, 'Name'),
              _field(context, profile.accountContact.mobilePhone, 'Mobile'),
              _field(context, profile.accountContact.homePhone, 'Home Phone'),
              _field(context, profile.accountContact.email, 'Email'),
              _field(context, profile.accountContact.addressLine1, 'Address'),
              _field(context, profile.accountContact.postalCode, 'Postal Code'),
            ]),
            _section('Results', [
              _field(context, profile.results.matricYear.toString(), 'Matric Year'),
              _field(context, profile.results.applicationLevel, 'Level'),
              _field(context, profile.results.matricType, 'Matric Type'),
              _field(context, profile.results.examinationNumber, 'Exam Number'),
              _field(context, profile.results.schoolLeavingCertificate, 'Leaving Certificate'),
            ]),
            _section('Qualification', [
              _field(context, profile.qualification.academicYear.toString(), 'Academic Year'),
              if (profile.qualification.choices.isNotEmpty) ...[
                _field(context, profile.qualification.choices.first.faculty, 'Faculty'),
                _field(context, profile.qualification.choices.first.programme, 'Programme'),
              ],
              _field(context, profile.qualification.applicationPeriod, 'Period'),
              _field(context, profile.qualification.studyMode, 'Study Mode'),
            ]),
            if (profile.results.subjects.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Text('Subjects', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
              const SizedBox(height: 4),
              ...profile.results.subjects.map((s) =>
                _field(context, s.subject, s.grade, trailing: '${s.result} ${s.symbol}')),
            ],
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _section(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary)),
        ),
        const SizedBox(height: 4),
        ...children,
      ],
    );
  }

  Widget _field(BuildContext context, String value, String label, {String? trailing}) {
    if (value.isEmpty) return const SizedBox.shrink();
    return InkWell(
      onTap: () {
        Clipboard.setData(ClipboardData(text: value));
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Copied: $value'), duration: const Duration(seconds: 1), backgroundColor: AppColors.success),
        );
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        child: Row(
          children: [
            SizedBox(
              width: 110,
              child: Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
            ),
            Expanded(
              child: Text(value, style: const TextStyle(fontSize: 13, color: AppColors.textPrimary)),
            ),
            if (trailing != null)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: Text(trailing, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
              ),
            Icon(Icons.copy_rounded, size: 14, color: AppColors.primary.withValues(alpha: 0.6)),
          ],
        ),
      ),
    );
  }
}
