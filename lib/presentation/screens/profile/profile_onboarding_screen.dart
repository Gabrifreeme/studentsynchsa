import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/constants/app_constants.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';

import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';
import 'package:studentsyncsa/models/postal_code.dart';
import 'package:studentsyncsa/widgets/postal_code_picker.dart';
import 'package:uuid/uuid.dart';

class ProfileOnboardingScreen extends ConsumerStatefulWidget {
  const ProfileOnboardingScreen({super.key});

  @override
  ConsumerState<ProfileOnboardingScreen> createState() =>
      _ProfileOnboardingScreenState();
}

class _ProfileOnboardingScreenState
    extends ConsumerState<ProfileOnboardingScreen>
    with SingleTickerProviderStateMixin {
  final _pageController = PageController();
  int _currentPage = 0;
  bool _showGreeting = true;
  int _visibleChars = 0;
  late AnimationController _floatCtrl;
  late Animation<double> _floatAnim;



  // Page 2 - Biographical
  String _isSACitizen = '';
  final _citizenshipCodeCtrl = TextEditingController();
  final _idNumberCtrl = TextEditingController();
  String _gender = '';
  DateTime? _selectedDob;
  String _title = '';
  final _initialsCtrl = TextEditingController();
  final _surnameCtrl = TextEditingController();
  final _firstNamesCtrl = TextEditingController();
  final _maidenNameCtrl = TextEditingController();
  String _maritalStatus = '';
  final _homeLanguageCtrl = TextEditingController();
  String _ethnicGroup = '';
  String _isEmployed = '';
  String _bursaryRequired = '';
  final _heardAboutUsCtrl = TextEditingController();

  // Page 3 - Address + Contact + Residence + Disability
  final _streetAddr1Ctrl = TextEditingController();
  final _streetAddr2Ctrl = TextEditingController();
  final _streetAddr3Ctrl = TextEditingController();
  String _streetProvince = '';
  final _streetPostalCodeCtrl = TextEditingController();
  final _streetPostalCodeConfirmCtrl = TextEditingController();
  bool _postalDifferent = false;
  final _postalAddr1Ctrl = TextEditingController();
  final _postalAddr2Ctrl = TextEditingController();
  final _postalAddr3Ctrl = TextEditingController();
  String _postalProvince = '';
  final _postalPostalCodeCtrl = TextEditingController();
  String _hasSACellphone = '';
  final _workPhoneCtrl = TextEditingController();
  final _homePhoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _verifyEmailCtrl = TextEditingController();
  String _wantsResidence = '';
  bool _hasDisability = false;

  // Page 4 - Results
  int _matricYear = 0;
  String _applicationLevel = '';
  String _isUpgrading = '';
  String _matricType = '';
  final _examNumberCtrl = TextEditingController();
  final _schoolLeavingCertCtrl = TextEditingController();
  String get _schoolLeavingCertificate => _schoolLeavingCertCtrl.text;
  set _schoolLeavingCertificate(String v) => _schoolLeavingCertCtrl.text = v;
  List<SubjectDetail> _resultsSubjects = [];
  final _subjectCtrl = TextEditingController();
  final _gradeCtrl = TextEditingController();
  String _subjectResult = '';
  String _subjectSymbol = '';
  int _subjectResetKey = 0;

  // Page 5 - Qualifications
  int _academicYear = 0;
  final _facultyCtrl = TextEditingController();
  final _programmeCtrl = TextEditingController();
  String _applicationPeriod = '';
  String _studyMode = '';
  String _studyTiming = '';
  String _applicationType = 'AT';
  String _applicationTypeDesc = 'SA Undergrad Applicant - Currently Gr 12';
  int _numAppsAllowed = 4;
  List<QualificationChoice> _qualificationChoices = [];

  // Page 1 - Next of Kin
  final _nextOfKinNameCtrl = TextEditingController();
  final _nextOfKinMobileCtrl = TextEditingController();
  final _nextOfKinHomePhoneCtrl = TextEditingController();
  final _nextOfKinWorkPhoneCtrl = TextEditingController();
  final _nextOfKinAddr1Ctrl = TextEditingController();
  final _nextOfKinAddr2Ctrl = TextEditingController();
  final _nextOfKinAddr3Ctrl = TextEditingController();
  final _nextOfKinAddr4Ctrl = TextEditingController();
  final _nextOfKinPostalCodeCtrl = TextEditingController();
  final _nextOfKinEmailCtrl = TextEditingController();

  // Account Contact
  final _accountContactNameCtrl = TextEditingController();
  final _accountContactMobileCtrl = TextEditingController();
  final _accountContactHomePhoneCtrl = TextEditingController();
  final _accountContactAddr1Ctrl = TextEditingController();
  final _accountContactAddr2Ctrl = TextEditingController();
  final _accountContactAddr3Ctrl = TextEditingController();
  final _accountContactAddr4Ctrl = TextEditingController();
  final _accountContactPostalCodeCtrl = TextEditingController();
  final _accountContactEmailCtrl = TextEditingController();

  bool _saving = false;

  final _formKeys = List.generate(3, (_) => GlobalKey<FormState>());
  static const _greetingText =
      "Hi there! I'm Star ⭐\n\nLet's get to know you so I can help find the perfect universities and bursaries for your future!";


  static const _languages = [
    'AFRIKAANS',
    'AFRIKAANS/ENGLISH',
    'ENGLISH',
    'HINDU',
    'OTHER BLACK LANG',
    'OTHER EUROPEAN LANG',
    'SOTHO(NORTH)',
    'SOTHO(SOUTH)',
    'SWATI',
    'TSONGA',
    'TSWANA',
    'UNKNOWN',
    'VENDA',
    'XHOSA',
    'ZULU',
  ];


  static const _schoolSubjects = [
    'ABRSM Practical Music',
    'Accounting',
    'Afrikaans First Add Language',
    'Afrikaans Home Language',
    'Afrikaans Second Add Language',
    'Agricultural Management Pract',
    'Agricultural Science',
    'Agricultural Technology',
    'Arabic Second Add Language',
    'Business Studies',
    'Civil Technology',
    'Computer Applications Tech',
    'Consumer Studies',
    'Dance Studies',
    'Design',
    'DiElectrical Technology',
    'Dramatic Arts',
    'Economics',
    'ElEletrical Technology',
    'Electrical Technology',
    'Engineering Graphics + Design',
    'English First Add Language',
    'English Home Language',
    'English Second Add Language',
    'Equine Studies',
    'French Second Add Language',
    'Geography',
    'German Home Language',
    'German Second Add Language',
    'Gujarati First Add Language',
    'Gujarati Home Language',
    'Gujarati Second Add Language',
    'Hebrew Second Add Language',
    'Hindi First Add Language',
    'Hindi Home Language',
    'Hindi Second Add Language',
    'History',
    'Hospitality Studies',
    'HoutbCivil Technology',
    'Information Technology',
    'IsiNdebele First Add Language',
    'IsiNdebele Home Language',
    'IsiNdebele Second Add Language',
    'IsiXhosa First Add Language',
    'IsiXhosa Home Language',
    'IsiXhosa Second Add Language',
    'IsiZulu First Add Language',
    'IsiZulu Home Language',
    'IsiZulu Second Add Language',
    'Italian Second Add Language',
    'KonstCivil Technology',
    'KrElectrical Technology',
    'Latin Second Add Language',
    'Life Orientation',
    'Life Sciences',
    'Mandarin Second Additional',
    'Marine Sciences',
    'Maritime Economics',
    'Mathematical Literacy',
    'Mathematics',
    'Mathematics (Third Paper)',
    'Mechanical Technology',
    'MoMechanical Technology',
    'Modern Greek Second Add Lang',
    'Music',
    'Nautical Science',
    'PasMechanical Technology',
    'Physical Sciences',
    'Portuguese First Add Language',
    'Portuguese Home Language',
    'Portuguese Second Add Language',
    'Religion Studies',
    'Sepedi First Add Language',
    'Sepedi Home Language',
    'Sepedi Second Add Language',
    'Sesotho First Add Language',
    'Sesotho Home Language',
    'Sesotho Second Add Language',
    'Setswana First Add Language',
    'Setswana Home Language',
    'Setswana Second Add Language',
    'SiSwati First Add Language',
    'SiSwati Home Language',
    'SiSwati Second Add Language',
    'SivieCivil Technology',
    'SpElectricall Technology',
    'Spanish Second Add Language',
    'SpeMechanical Technology',
    'SpesiCivil Technology',
    'Sport and Exercise Science',
    'SweMechanical Technology',
    'TCL Practical Grade',
    'TECHNICAL DRAWING',
    'TRAVEL AND TOURISM SG',
    'Tamil First Add Language',
    'Tamil Home Language',
    'Tamil Second Add Language',
    'Technical Methematics',
    'Technical Sciences',
    'Telegu First Add Language',
    'Telegu Home Language',
    'Telegu Second Add Language',
    'Tourism',
    'Tshivenda First Add Language',
    'Tshivenda Home Language',
    'Tshivenda Second Add Language',
    'UNISA Practical Music',
    'Urdu First Add Language',
    'Urdu Home Language',
    'Urdu Second Add Language',
    'Visual Arts',
    'Xitsonga First Add Language',
    'Xitsonga Home Language',
    'Xitsonga Second Add Language',
  ];


  @override
  void initState() {
    super.initState();
    _floatCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _floatAnim = Tween<double>(
      begin: -8,
      end: 8,
    ).animate(CurvedAnimation(parent: _floatCtrl, curve: Curves.easeInOut));
    _startTextReveal();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadExistingProfile());
  }

  void _loadExistingProfile() async {
    var profile =
        ref.read(profileProvider).valueOrNull ??
        ref.read(authProvider).valueOrNull?.profile;
    if (profile == null) {
      // Try reading directly from Hive in case providers haven't loaded yet
      try {
        profile = await ProfileRepositoryImpl().getProfile();
      } catch (_) {}
    }
    if (profile == null) {
      // Retry once after a short delay
      await Future.delayed(const Duration(milliseconds: 500));
      profile =
          ref.read(profileProvider).valueOrNull ??
          ref.read(authProvider).valueOrNull?.profile;
      if (profile == null) {
        try {
          profile = await ProfileRepositoryImpl().getProfile();
        } catch (_) {}
      }
    }
    if (profile == null) return;
    final p = profile;
    setState(() {
      _applyProfile(p);
    });
  }

  void _applyProfile(StudentProfile p) {
    _isSACitizen = [
      'SA Citizen',
      'Permanent Resident',
      'Foreign National',
    ].contains(p.demographic.nationality.trim())
        ? p.demographic.nationality.trim()
        : '';
    _citizenshipCodeCtrl.text = p.demographic.citizenshipCode;
    _idNumberCtrl.text = p.personal.idNumber;
    _gender = p.personal.gender.trim();
    _selectedDob = p.personal.dateOfBirth;
    _title = p.personal.title.trim();
    _initialsCtrl.text = p.personal.initials;
    _surnameCtrl.text = p.personal.lastName;
    _firstNamesCtrl.text = p.personal.firstName;
    _maidenNameCtrl.text = p.personal.maidenName;
    _maritalStatus = p.demographic.maritalStatus.trim();
    _homeLanguageCtrl.text = p.demographic.homeLanguage;
    final rawPop = p.demographic.populationGroup.trim();
    _ethnicGroup = rawPop == 'Black' ? 'African' : rawPop;
    final es = p.status.employmentStatus.trim();
    _isEmployed = const {
      'Unemployed',
      'Employed (part-time)',
      'Employed (full-time)',
      'Self-employed',
    }.contains(es)
        ? es
        : '';
    _bursaryRequired = p.status.bursaryRequired.trim();
    _heardAboutUsCtrl.text = p.demographic.heardAboutUs;
    _streetAddr1Ctrl.text = p.address.address;
    _streetAddr2Ctrl.text = p.address.addressLine2;
    _streetAddr3Ctrl.text = p.address.addressLine3;
    _streetProvince = p.address.province.trim();
    _streetPostalCodeCtrl.text = p.address.postalCode;
    _postalDifferent = p.address.postalAddress.isNotEmpty &&
        p.address.postalAddress != p.address.address;
    if (_postalDifferent) {
      final lines = p.address.postalAddress.split('\n');
      if (lines.isNotEmpty) _postalAddr1Ctrl.text = lines[0];
      if (lines.length > 1) _postalAddr2Ctrl.text = lines[1];
      if (lines.length > 2) _postalAddr3Ctrl.text = lines[2];
    }
    _hasSACellphone = p.contact.hasSACellphone;
    _workPhoneCtrl.text = p.contact.workPhone;
    _homePhoneCtrl.text = p.contact.phone;
    _emailCtrl.text = p.contact.email;
    _verifyEmailCtrl.text = p.contact.verifyEmail;
    _wantsResidence = p.status.wantsResidence;
    _hasDisability = p.status.disabilityStatus == 'Yes';
    _matricYear = p.results.matricYear;
    _applicationLevel = p.results.applicationLevel.trim();
    _isUpgrading = p.results.upgrading.trim();
    _matricType = p.results.matricType.trim();
    _examNumberCtrl.text = p.results.examinationNumber;
    _schoolLeavingCertificate = p.results.schoolLeavingCertificate;
    _resultsSubjects = p.results.subjects;
    _academicYear = p.qualification.academicYear;
    _facultyCtrl.text = p.qualification.choices.isNotEmpty ? p.qualification.choices.first.faculty : '';
    _programmeCtrl.text = p.qualification.choices.isNotEmpty ? p.qualification.choices.first.programme : '';
    _applicationPeriod = p.qualification.applicationPeriod.trim();
    _studyMode = p.qualification.studyMode.trim();
    _studyTiming = p.qualification.studyTiming.trim();
    _applicationType = p.qualification.applicationType;
    _applicationTypeDesc = p.qualification.applicationTypeDescription;
    _numAppsAllowed = p.qualification.numApplicationsAllowed;
    _qualificationChoices = p.qualification.choices;
    _nextOfKinNameCtrl.text = p.nextOfKin.name;
    _nextOfKinMobileCtrl.text = p.nextOfKin.mobilePhone;
    _nextOfKinHomePhoneCtrl.text = p.nextOfKin.homePhone;
    _nextOfKinWorkPhoneCtrl.text = p.nextOfKin.workPhone;
    _nextOfKinAddr1Ctrl.text = p.nextOfKin.addressLine1;
    _nextOfKinAddr2Ctrl.text = p.nextOfKin.addressLine2;
    _nextOfKinAddr3Ctrl.text = p.nextOfKin.addressLine3;
    _nextOfKinAddr4Ctrl.text = p.nextOfKin.addressLine4;
    _nextOfKinPostalCodeCtrl.text = p.nextOfKin.postalCode;
    _nextOfKinEmailCtrl.text = p.nextOfKin.email;
    _accountContactNameCtrl.text = p.accountContact.name;
    _accountContactMobileCtrl.text = p.accountContact.mobilePhone;
    _accountContactHomePhoneCtrl.text = p.accountContact.homePhone;
    _accountContactAddr1Ctrl.text = p.accountContact.addressLine1;
    _accountContactAddr2Ctrl.text = p.accountContact.addressLine2;
    _accountContactAddr3Ctrl.text = p.accountContact.addressLine3;
    _accountContactAddr4Ctrl.text = p.accountContact.addressLine4;
    _accountContactPostalCodeCtrl.text = p.accountContact.postalCode;
    _accountContactEmailCtrl.text = p.accountContact.email;
  }

  void _startTextReveal() {
    Future.delayed(const Duration(milliseconds: 500), () {
      const total = _greetingText.length;
      const interval = Duration(milliseconds: 30);
      Timer.periodic(interval, (timer) {
        if (_visibleChars >= total || !mounted) {
          timer.cancel();
          return;
        }
        setState(() => _visibleChars += 2);
      });
    });
  }

  void _dismissGreeting() {
    setState(() => _showGreeting = false);
  }

  static Future<String?> _showSearchablePicker(
    BuildContext context, {
    required String title,
    required List<String> options,
    String? initialValue,
    String? Function(String)? displayTransformer,
  }) {
    return showDialog<String>(
      context: context,
      builder: (ctx) {
        final searchCtrl = TextEditingController();
        String? selected = initialValue;
        final maxHeight = MediaQuery.of(ctx).size.height * 0.65;
        return StatefulBuilder(
          builder: (ctx, setDialogState) {
            final filtered = options.where((o) {
              final q = searchCtrl.text.toLowerCase();
              if (q.isEmpty) return true;
              return o.toLowerCase().contains(q);
            }).toList();
            return Dialog(
              backgroundColor: AppColors.surface,
              insetPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 40,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: maxHeight,
                  maxWidth: 480,
                ),
                child: Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 12, 8, 0),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              title,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.close),
                            tooltip: 'Cancel',
                            onPressed: () => Navigator.pop(ctx),
                          ),
                        ],
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                      child: TextField(
                        controller: searchCtrl,
                        autofocus: true,
                        decoration: InputDecoration(
                          hintText: 'Search $title...',
                          prefixIcon: const Icon(
                            Icons.search,
                            color: AppColors.textMuted,
                          ),
                          suffixIcon: searchCtrl.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear, size: 18),
                                  onPressed: () {
                                    searchCtrl.clear();
                                    setDialogState(() {});
                                  },
                                )
                              : null,
                        ),
                        onChanged: (_) => setDialogState(() {}),
                      ),
                    ),
                    const Divider(height: 1),
                    if (filtered.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(32),
                        child: Text(
                          'No results found',
                          style: TextStyle(color: AppColors.textMuted),
                        ),
                      )
                    else
                      Expanded(
                        child: ListView.builder(
                          itemCount: filtered.length,
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          itemBuilder: (_, i) {
                            final item = filtered[i];
                            final display =
                                displayTransformer?.call(item) ?? item;
                            return ListTile(
                              dense: true,
                              selected: selected == item,
                              selectedTileColor: AppColors.primary.withValues(
                                alpha: 0.08,
                              ),
                              title: Text(
                                display,
                                style: const TextStyle(
                                  fontSize: 14,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              onTap: () {
                                Navigator.pop(ctx, item);
                              },
                            );
                          },
                        ),
                      ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  void dispose() {
    _floatCtrl.dispose();
    _pageController.dispose();
    _initialsCtrl.dispose();
    _surnameCtrl.dispose();
    _firstNamesCtrl.dispose();
    _maidenNameCtrl.dispose();
    _citizenshipCodeCtrl.dispose();
    _idNumberCtrl.dispose();
    _heardAboutUsCtrl.dispose();
    _homeLanguageCtrl.dispose();
    _streetAddr1Ctrl.dispose();
    _streetAddr2Ctrl.dispose();
    _streetAddr3Ctrl.dispose();
    _streetPostalCodeCtrl.dispose();
    _streetPostalCodeConfirmCtrl.dispose();
    _postalAddr1Ctrl.dispose();
    _postalAddr2Ctrl.dispose();
    _postalAddr3Ctrl.dispose();
    _postalPostalCodeCtrl.dispose();
    _homePhoneCtrl.dispose();
    _workPhoneCtrl.dispose();
    _emailCtrl.dispose();
    _verifyEmailCtrl.dispose();
    _examNumberCtrl.dispose();
    _subjectCtrl.dispose();
    _gradeCtrl.dispose();
    _schoolLeavingCertCtrl.dispose();
    _facultyCtrl.dispose();
    _programmeCtrl.dispose();
    _nextOfKinNameCtrl.dispose();
    _nextOfKinMobileCtrl.dispose();
    _nextOfKinHomePhoneCtrl.dispose();
    _nextOfKinWorkPhoneCtrl.dispose();
    _nextOfKinAddr1Ctrl.dispose();
    _nextOfKinAddr2Ctrl.dispose();
    _nextOfKinAddr3Ctrl.dispose();
    _nextOfKinAddr4Ctrl.dispose();
    _nextOfKinPostalCodeCtrl.dispose();
    _nextOfKinEmailCtrl.dispose();
    _accountContactNameCtrl.dispose();
    _accountContactMobileCtrl.dispose();
    _accountContactHomePhoneCtrl.dispose();
    _accountContactAddr1Ctrl.dispose();
    _accountContactAddr2Ctrl.dispose();
    _accountContactAddr3Ctrl.dispose();
    _accountContactAddr4Ctrl.dispose();
    _accountContactPostalCodeCtrl.dispose();
    _accountContactEmailCtrl.dispose();
    super.dispose();
  }

  bool _validateCurrentPage() {
    return _formKeys[_currentPage].currentState?.validate() ?? false;
  }

  Future<void> _saveAndContinue() async {
    if (!_validateCurrentPage()) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please fill in all required fields'),
            duration: Duration(seconds: 2),
            backgroundColor: AppColors.error,
          ),
        );
      }
      return;
    }
    if (_currentPage < 2) {
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
    try {
      final authState = ref.read(authProvider);
      final existingProfile = authState.value?.profile;
      final id = existingProfile?.id ?? const Uuid().v4();

      final profile = StudentProfile(
        id: id,
        personal: PersonalDetails(
          title: _title,
          initials: _initialsCtrl.text.trim(),
          firstName: _firstNamesCtrl.text.trim(),
          lastName: _surnameCtrl.text.trim(),
          maidenName: _maidenNameCtrl.text.trim(),
          gender: _gender,
          dateOfBirth: _selectedDob,
          idNumber: _idNumberCtrl.text.trim(),
        ),
        contact: ContactInfo(
          email: _emailCtrl.text.trim(),
          phone: _homePhoneCtrl.text.trim(),
          workPhone: _workPhoneCtrl.text.trim(),
          hasSACellphone: _hasSACellphone,
          verifyEmail: _verifyEmailCtrl.text.trim(),
        ),
        address: AddressInfo(
          address: _streetAddr1Ctrl.text.trim(),
          addressLine2: _streetAddr2Ctrl.text.trim(),
          addressLine3: _streetAddr3Ctrl.text.trim(),
          province: _streetProvince,
          postalCode: _streetPostalCodeCtrl.text.trim(),
          postalAddress: _postalDifferent
              ? _postalAddr1Ctrl.text.trim()
              : _streetAddr1Ctrl.text.trim(),
        ),
        demographic: DemographicInfo(
          nationality: _isSACitizen,
          homeLanguage: _homeLanguageCtrl.text.trim(),
          populationGroup: _ethnicGroup,
          maritalStatus: _maritalStatus,
          citizenshipCode: _citizenshipCodeCtrl.text.trim(),
          heardAboutUs: _heardAboutUsCtrl.text.trim(),
        ),
        status: StatusInfo(
          disabilityStatus: _hasDisability ? 'Yes' : 'No',
          bursaryRequired: _bursaryRequired,
          employmentStatus: _isEmployed,
          wantsResidence: _wantsResidence,
        ),
        nextOfKin: NextOfKin(
          name: _nextOfKinNameCtrl.text.trim(),
          mobilePhone: _nextOfKinMobileCtrl.text.trim(),
          homePhone: _nextOfKinHomePhoneCtrl.text.trim(),
          workPhone: _nextOfKinWorkPhoneCtrl.text.trim(),
          addressLine1: _nextOfKinAddr1Ctrl.text.trim(),
          addressLine2: _nextOfKinAddr2Ctrl.text.trim(),
          addressLine3: _nextOfKinAddr3Ctrl.text.trim(),
          addressLine4: _nextOfKinAddr4Ctrl.text.trim(),
          postalCode: _nextOfKinPostalCodeCtrl.text.trim(),
          email: _nextOfKinEmailCtrl.text.trim(),
        ),
        accountContact: AccountContact(
          name: _accountContactNameCtrl.text.trim(),
          mobilePhone: _accountContactMobileCtrl.text.trim(),
          homePhone: _accountContactHomePhoneCtrl.text.trim(),
          addressLine1: _accountContactAddr1Ctrl.text.trim(),
          addressLine2: _accountContactAddr2Ctrl.text.trim(),
          addressLine3: _accountContactAddr3Ctrl.text.trim(),
          addressLine4: _accountContactAddr4Ctrl.text.trim(),
          postalCode: _accountContactPostalCodeCtrl.text.trim(),
          email: _accountContactEmailCtrl.text.trim(),
        ),
        results: ResultsInfo(
          matricYear: _matricYear,
          applicationLevel: _applicationLevel,
          upgrading: _isUpgrading,
          matricType: _matricType,
          examinationNumber: _examNumberCtrl.text.trim(),
          schoolLeavingCertificate: _schoolLeavingCertificate,
          subjects: _resultsSubjects,
        ),
        qualification: QualificationInfo(
          academicYear: _academicYear,
          choices: _qualificationChoices,
          applicationPeriod: _applicationPeriod,
          studyMode: _studyMode,
          studyTiming: _studyTiming,
          applicationType: _applicationType,
          applicationTypeDescription: _applicationTypeDesc,
          numApplicationsAllowed: _numAppsAllowed,
        ),
        onboardingComplete: true,
      );

      await ref.read(profileProvider.notifier).saveProfile(profile);
      if (mounted) {
        setState(() => _saving = false);
        context.go('/dashboard');
      }
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to save profile: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Widget _buildProgressBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        children: List.generate(5, (i) {
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
    if (_showGreeting) {
      return GradientBackground(
        child: Scaffold(
          backgroundColor: Colors.transparent,
          body: SafeArea(
            child: GestureDetector(
              onTap: _dismissGreeting,
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 40),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AnimatedBuilder(
                        animation: _floatAnim,
                        builder: (context, child) {
                          return Transform.translate(
                            offset: Offset(0, _floatAnim.value),
                            child: child,
                          );
                        },
                        child: const StarAvatar(size: 96, pulse: true),
                      ),
                      const SizedBox(height: 40),
                      Text(
                        _greetingText.substring(
                          0,
                          _visibleChars.clamp(0, _greetingText.length),
                        ),
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 20,
                          height: 1.6,
                        ),
                      ),
                      const SizedBox(height: 48),
                      if (_visibleChars >= _greetingText.length)
                        ElevatedButton.icon(
                          onPressed: _dismissGreeting,
                          icon: const Icon(Icons.arrow_forward_rounded),
                          label: const Text("Let's Get Started"),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.starGold,
                            foregroundColor: Colors.black,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 32,
                              vertical: 16,
                            ),
                            textStyle: const TextStyle(fontSize: 16),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      );
    }

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
        body: Stack(
          children: [
            Column(
              children: [
                _buildProgressBar(),
                Text(
                  'Step ${_currentPage + 1} of 3',
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
                      _buildPage1BiographicalCombined(),
                      _buildPage4Results(),
                      _buildPage5Qualifications(),
                    ],
                  ),
                ),
                _buildBottomButtons(),
              ],
            ),
            // Floating Star avatar
            Positioned(
              right: 16,
              bottom: 100,
              child: GestureDetector(
                onTap: _showStarHelp,
                child: AnimatedBuilder(
                  animation: _floatAnim,
                  builder: (context, child) {
                    return Transform.translate(
                      offset: Offset(0, _floatAnim.value),
                      child: child,
                    );
                  },
                  child: Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.starGold.withValues(alpha: 0.4),
                          blurRadius: 12,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: const StarAvatar(size: 48, pulse: true),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showStarHelp() {
    final tips = [
      'Tell Star about yourself! Your name, ID, and contact info help universities reach you.',
      'Your school and grade info help Star recommend the right programmes.',
      'Add your Grade 12 (or Grade 11) subjects and marks so Star can calculate your APS score.',
      'Pick your interests and career goals — Star will find the best match for you!',
    ];
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            StarAvatar(size: 28),
            SizedBox(width: 8),
            Text('Star says:', style: TextStyle(color: AppColors.starGold)),
          ],
        ),
        content: Text(
          tips[_currentPage.clamp(0, tips.length - 1)],
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 15,
            height: 1.5,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text(
              'Got it!',
              style: TextStyle(color: AppColors.primaryLight),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPage1BiographicalCombined() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[0],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Biographical Details'),
            const SizedBox(height: 16),
            const Text(
              'In this section you are required to enter your biographical details.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 20),
            const Text(
              'Nationality',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 4),
            const Text(
              'Please select your current nationality and capture your ID or passport number.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _isSACitizen.isEmpty ? null : _isSACitizen,
              decoration: const InputDecoration(
                labelText: 'Are you a SA Citizen in possession of a valid SA ID/Birth Certificate? *',
                prefixIcon: Icon(Icons.flag_outlined),
              ),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'SA Citizen', child: Text('SA Citizen')),
                DropdownMenuItem(value: 'Permanent Resident', child: Text('Permanent Resident')),
                DropdownMenuItem(value: 'Foreign National', child: Text('Foreign National')),
              ],
              onChanged: (v) => setState(() => _isSACitizen = v ?? ''),
              validator: (v) => v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _citizenshipCodeCtrl,
              decoration: const InputDecoration(
                labelText: 'Citizenship Code *',
                prefixIcon: Icon(Icons.badge_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              readOnly: true,
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                const codes = [
                  'RSA - South Africa',
                  'AFGHANISTAN',
                  'ALBANIA',
                  'ALGERIA',
                  'ALGERIA',
                  'ANDORRA',
                  'ANGOLA',
                  'ANTIGUA AND BARBUDA',
                  'ARGENTINA',
                  'ARMENIA',
                  'AUSTRALIA',
                  'AUSTRIA',
                  'AZERBAIJAN',
                  'BAHAMAS',
                  'BAHRAIN',
                  'BANGLADESH',
                  'BARBADOS',
                  'BELARUS',
                  'BELGIUM',
                  'BELIZE',
                  'BENIN',
                  'BHUTAN',
                  'BOLIVIA',
                  'BOSNIA AND HERZEGOVINA',
                  'BOTSWANA',
                  'BRAZIL',
                  'BURKINA FASO',
                  'BURUNDI',
                  'CAMEROON',
                  'CAPE VERDE',
                  'CENTRAL AFRICAN REPUBLIC',
                  'CHAD',
                  'CORTE de VOIRE',
                  'COUNTRIES IN ASIA',
                  'COUNTRIES IN AUSTRALASIA AND OCEANIA',
                  'COUNTRIES IN EUROPE',
                  'COUNTRIES IN NORTH AMERICA',
                  'COUNTRIES IN SOUTH AMERICA',
                  'DJIBOUTI',
                  'Democratic Republic of the Congo',
                  'EGYPT',
                  'EQUATORIAL GUINEA',
                  'ERITREA',
                  'ETHIOPIA',
                  'FRANCE',
                  'GABON',
                  'GAMBIA',
                  'GERMANY',
                  'GHANA',
                  'GUINEA BISAU',
                  'INDIA',
                  'ITALY',
                  'KENYA',
                  'LESOTHO',
                  'LIBERIA',
                  'LIBYA',
                  'MADAGASCAR',
                  'MALAWI',
                  'MALI',
                  'MAURITANIA',
                  'MAURITIUS',
                  'MOROCCO',
                  'MOZAMBIQUE',
                  'NAMIBIA',
                  'NIGER',
                  'NIGERIA',
                  'OTHER AFRICAN COUNTRIES',
                  'RWANDA',
                  'SENEGAL',
                  'SEYCHELLES',
                  'SIERRA LEONE',
                  'SUDAN',
                  'SWAZILAND',
                  'TANZANIA',
                  'TOGO',
                  'TUNISIA',
                  'UGANDA',
                  'UNITED ARAB EMIRATES',
                  'ZAMBIA',
                  'ZIMBABWE',
                ];
                final result = await _showSearchablePicker(context, title: 'Citizenship Code', options: codes, initialValue: _citizenshipCodeCtrl.text.isNotEmpty ? _citizenshipCodeCtrl.text : 'RSA');
                if (result != null) setState(() => _citizenshipCodeCtrl.text = result);
              },
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _idNumberCtrl,
              keyboardType: TextInputType.text,
              decoration: const InputDecoration(
                labelText: 'ID / Passport Number *',
                prefixIcon: Icon(Icons.perm_identity_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 24),
            const Text('Personal Information', style: TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            const Text('Please enter your personal information.', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _gender.isEmpty ? null : _gender,
              decoration: const InputDecoration(labelText: 'Gender *', prefixIcon: Icon(Icons.wc_outlined)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'Male', child: Text('Male')),
                DropdownMenuItem(value: 'Female', child: Text('Female')),
                DropdownMenuItem(value: 'Other', child: Text('Other')),
                DropdownMenuItem(value: 'Prefer not to say', child: Text('Prefer not to say')),
              ],
              onChanged: (v) => setState(() => _gender = v ?? ''),
              validator: (v) => v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            InkWell(
              onTap: () async {
                final picked = await showDatePicker(
                  context: context, initialDate: _selectedDob ?? DateTime(2006),
                  firstDate: DateTime(1950), lastDate: DateTime.now(),
                  builder: (ctx, child) => Theme(
                    data: Theme.of(context).copyWith(colorScheme: const ColorScheme.dark(primary: AppColors.primary, surface: AppColors.surface)),
                    child: child!,
                  ),
                );
                if (picked != null) setState(() => _selectedDob = picked);
              },
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: 'Date of birth (DD-MON-YYYY) *',
                  prefixIcon: const Icon(Icons.calendar_today_outlined),
                  suffixIcon: _selectedDob != null
                      ? IconButton(icon: const Icon(Icons.clear, size: 18), onPressed: () => setState(() => _selectedDob = null))
                      : null,
                ),
                child: Text(
                  _selectedDob != null ? '${_selectedDob!.day}/${_selectedDob!.month}/${_selectedDob!.year}' : '',
                  style: const TextStyle(color: AppColors.textPrimary),
                ),
              ),
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _title.isEmpty ? null : _title,
              decoration: const InputDecoration(labelText: 'Title *', prefixIcon: Icon(Icons.badge_outlined, size: 20)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'Mr', child: Text('Mr')),
                DropdownMenuItem(value: 'Mrs', child: Text('Mrs')),
                DropdownMenuItem(value: 'Ms', child: Text('Ms')),
              ],
              onChanged: (v) => setState(() => _title = v ?? ''),
              validator: (v) => v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(controller: _initialsCtrl, decoration: const InputDecoration(labelText: 'Initials *', prefixIcon: Icon(Icons.short_text, size: 20)), validator: (v) => v?.trim().isEmpty == true ? 'Required' : null),
            const SizedBox(height: 14),
            TextFormField(controller: _surnameCtrl, decoration: const InputDecoration(labelText: 'Surname *', prefixIcon: Icon(Icons.person_outline)), validator: (v) => v?.trim().isEmpty == true ? 'Required' : null),
            const SizedBox(height: 14),
            TextFormField(controller: _firstNamesCtrl, decoration: const InputDecoration(labelText: 'First names *', prefixIcon: Icon(Icons.person_outline)), validator: (v) => v?.trim().isEmpty == true ? 'Required' : null),
            const SizedBox(height: 14),
            TextFormField(controller: _maidenNameCtrl, decoration: const InputDecoration(labelText: 'Maiden name', prefixIcon: Icon(Icons.person_outline))),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _maritalStatus.isEmpty ? null : _maritalStatus,
              decoration: const InputDecoration(labelText: 'Marital status *', prefixIcon: Icon(Icons.favorite_outline)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'Single', child: Text('Single')),
                DropdownMenuItem(value: 'Married', child: Text('Married')),
                DropdownMenuItem(value: 'Divorced', child: Text('Divorced')),
                DropdownMenuItem(value: 'Widowed', child: Text('Widowed')),
              ],
              onChanged: (v) => setState(() => _maritalStatus = v ?? ''),
              validator: (v) => v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _homeLanguageCtrl, readOnly: true,
              decoration: const InputDecoration(labelText: 'Home language *', prefixIcon: Icon(Icons.language_outlined), suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted)),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await _showSearchablePicker(context, title: 'Language', options: _languages, initialValue: _homeLanguageCtrl.text);
                if (result != null) setState(() => _homeLanguageCtrl.text = result);
              },
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _ethnicGroup.isEmpty ? null : _ethnicGroup,
              decoration: const InputDecoration(labelText: 'Ethnic group *', prefixIcon: Icon(Icons.people_outlined)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'African', child: Text('African')),
                DropdownMenuItem(value: 'Coloured', child: Text('Coloured')),
                DropdownMenuItem(value: 'Indian/Asian', child: Text('Indian/Asian')),
                DropdownMenuItem(value: 'White', child: Text('White')),
                DropdownMenuItem(value: 'Other', child: Text('Other')),
                DropdownMenuItem(value: 'Prefer not to say', child: Text('Prefer not to say')),
              ],
              onChanged: (v) => setState(() => _ethnicGroup = v ?? ''),
              validator: (v) => v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _isEmployed.isEmpty ? null : _isEmployed,
              decoration: const InputDecoration(labelText: 'Are you Employed?', prefixIcon: Icon(Icons.work_outline)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'Unemployed', child: Text('Unemployed')),
                DropdownMenuItem(value: 'Employed (part-time)', child: Text('Employed (part-time)')),
                DropdownMenuItem(value: 'Employed (full-time)', child: Text('Employed (full-time)')),
                DropdownMenuItem(value: 'Self-employed', child: Text('Self-employed')),
              ],
              onChanged: (v) => setState(() => _isEmployed = v ?? ''),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _heardAboutUsCtrl, readOnly: true,
              decoration: const InputDecoration(labelText: 'Where did you hear about us?', prefixIcon: Icon(Icons.info_outlined), suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted)),
              onTap: () async {
                const sources = ['--- Please select ---', 'Radio', 'Television', 'Newspaper', 'Internet', 'Friend/Family', 'School/Teacher', 'Career Fair', 'Social Media', 'Other'];
                final result = await _showSearchablePicker(context, title: 'Source', options: sources, initialValue: _heardAboutUsCtrl.text);
                if (result != null) setState(() => _heardAboutUsCtrl.text = result);
              },
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _bursaryRequired.isEmpty ? null : _bursaryRequired,
              decoration: const InputDecoration(labelText: 'Is a bursary required?', prefixIcon: Icon(Icons.monetization_on_outlined)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'Yes', child: Text('Yes')),
                DropdownMenuItem(value: 'No', child: Text('No')),
                DropdownMenuItem(value: 'Unsure', child: Text('Unsure')),
              ],
              onChanged: (v) => setState(() => _bursaryRequired = v ?? ''),
            ),
            const SizedBox(height: 28),
            Container(width: double.infinity, height: 1, color: AppColors.border),
            const SizedBox(height: 20),
            const Text('Address Information', style: TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Please enter your address information.', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 16),
            const Text('Street Address', style: TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            TextFormField(controller: _streetAddr1Ctrl, decoration: const InputDecoration(labelText: 'Street Address Line 1 (e.g. Street Name) *', prefixIcon: Icon(Icons.home_outlined)), validator: (v) => v?.trim().isEmpty == true ? 'Required' : null),
            const SizedBox(height: 14),
            TextFormField(controller: _streetAddr2Ctrl, decoration: const InputDecoration(labelText: 'Street Address Line 2 (e.g. Suburb Name) *', prefixIcon: Icon(Icons.home_outlined)), validator: (v) => v?.trim().isEmpty == true ? 'Required' : null),
            const SizedBox(height: 14),
            TextFormField(controller: _streetAddr3Ctrl, decoration: const InputDecoration(labelText: 'Street Address Line 3 (e.g. Town Name)', prefixIcon: Icon(Icons.home_outlined))),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _streetProvince.isEmpty ? null : _streetProvince,
              decoration: const InputDecoration(labelText: 'Street Address Line 4 (Province Name) *', prefixIcon: Icon(Icons.map_outlined)),
              items: AppConstants.provinces.map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
              onChanged: (v) => setState(() => _streetProvince = v ?? ''),
              validator: (v) => v == null ? 'Select your province' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _streetPostalCodeCtrl,
              decoration: const InputDecoration(labelText: 'Postal Code *', prefixIcon: Icon(Icons.pin_outlined), suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted)),
              readOnly: true,
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await showPostalCodePicker(
                  context: context,
                  initial: _streetPostalCodeCtrl.text.isEmpty
                      ? null
                      : PostalCode(
                          code: _streetPostalCodeCtrl.text,
                          description: _streetPostalCodeCtrl.text,
                        ),
                );
                if (result != null) {
                  setState(() => _streetPostalCodeCtrl.text = result.code);
                }
              },
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _streetPostalCodeConfirmCtrl,
              decoration: const InputDecoration(labelText: 'Confirm Postal Code *', prefixIcon: Icon(Icons.pin_outlined)),
              validator: (v) {
                if (v?.trim().isEmpty == true) return 'Required';
                if (v!.trim() != _streetPostalCodeCtrl.text.trim()) return 'Postal codes do not match';
                return null;
              },
            ),
            const SizedBox(height: 8),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Tick if your Postal Address is different from your Street Address', style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
              value: _postalDifferent,
              onChanged: (v) => setState(() => _postalDifferent = v ?? false),
              controlAffinity: ListTileControlAffinity.leading, dense: true,
            ),
            if (_postalDifferent) ...[
              const SizedBox(height: 12),
              const Text('Postal Address', style: TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
              const SizedBox(height: 12),
              TextFormField(controller: _postalAddr1Ctrl, decoration: const InputDecoration(labelText: 'Postal Address Line 1 *', prefixIcon: Icon(Icons.mail_outlined)), validator: (v) => _postalDifferent && v?.trim().isEmpty == true ? 'Required' : null),
              const SizedBox(height: 14),
              TextFormField(controller: _postalAddr2Ctrl, decoration: const InputDecoration(labelText: 'Postal Address Line 2 *', prefixIcon: Icon(Icons.mail_outlined)), validator: (v) => _postalDifferent && v?.trim().isEmpty == true ? 'Required' : null),
              const SizedBox(height: 14),
              TextFormField(controller: _postalAddr3Ctrl, decoration: const InputDecoration(labelText: 'Postal Address Line 3', prefixIcon: Icon(Icons.mail_outlined))),
              const SizedBox(height: 14),
              DropdownButtonFormField<String>(
                initialValue: _postalProvince.isEmpty ? null : _postalProvince,
                decoration: const InputDecoration(labelText: 'Postal Address Line 4 (Province) *', prefixIcon: Icon(Icons.map_outlined)),
                items: AppConstants.provinces.map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                onChanged: (v) => setState(() => _postalProvince = v ?? ''),
                validator: (v) => _postalDifferent && v == null ? 'Select province' : null,
              ),
              const SizedBox(height: 14),
              TextFormField(
                controller: _postalPostalCodeCtrl,
                decoration: const InputDecoration(labelText: 'Postal Code *', prefixIcon: Icon(Icons.pin_outlined), suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted)),
                readOnly: true,
                validator: (v) => _postalDifferent && v?.trim().isEmpty == true ? 'Required' : null,
                onTap: () async {
                final result = await showPostalCodePicker(
                  context: context,
                  initial: _postalPostalCodeCtrl.text.isEmpty
                      ? null
                      : PostalCode(
                          code: _postalPostalCodeCtrl.text,
                          description: _postalPostalCodeCtrl.text,
                        ),
                );
                if (result != null) {
                  setState(() => _postalPostalCodeCtrl.text = result.code);
                }
                },
              ),
            ],
            const SizedBox(height: 28),
            Container(width: double.infinity, height: 1, color: AppColors.border),
            const SizedBox(height: 20),
            const Text('Contact Information', style: TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Please enter your contact information.', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            DropdownButtonFormField<String>(
              initialValue: _hasSACellphone.isEmpty ? null : _hasSACellphone,
              decoration: const InputDecoration(labelText: 'Do you have a South African Cell Phone Number? *', prefixIcon: Icon(Icons.phone_android_outlined)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'Yes', child: Text('Yes')),
                DropdownMenuItem(value: 'No', child: Text('No')),
              ],
              onChanged: (v) => setState(() => _hasSACellphone = v ?? ''),
              validator: (v) => v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(controller: _workPhoneCtrl, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Work Telephone Number', prefixIcon: Icon(Icons.phone_forwarded_outlined))),
            const SizedBox(height: 14),
            TextFormField(controller: _homePhoneCtrl, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Home Telephone Number', prefixIcon: Icon(Icons.phone_outlined))),
            const SizedBox(height: 14),
            TextFormField(controller: _emailCtrl, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email *', prefixIcon: Icon(Icons.email_outlined)), validator: (v) => v?.trim().isEmpty == true ? 'Required' : null),
            const SizedBox(height: 14),
            TextFormField(controller: _verifyEmailCtrl, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Verify email *', prefixIcon: Icon(Icons.email_outlined)), validator: (v) {
              if (v?.trim().isEmpty == true) return 'Required';
              if (v!.trim() != _emailCtrl.text.trim()) return 'Emails do not match';
              return null;
            }),
            const SizedBox(height: 28),
            Container(width: double.infinity, height: 1, color: AppColors.border),
            const SizedBox(height: 20),
            const Text('Residence Information', style: TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Please select whether you want to apply for residence.', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _wantsResidence.isEmpty ? null : _wantsResidence,
              decoration: const InputDecoration(labelText: 'Do you want to apply for residence? *', prefixIcon: Icon(Icons.bed_outlined)),
              items: const [
                DropdownMenuItem(value: '--- Please select ---', child: Text('--- Please select ---')),
                DropdownMenuItem(value: 'Yes', child: Text('Yes')),
                DropdownMenuItem(value: 'No', child: Text('No')),
              ],
              onChanged: (v) => setState(() => _wantsResidence = v ?? ''),
              validator: (v) => v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 28),
            Container(width: double.infinity, height: 1, color: AppColors.border),
            const SizedBox(height: 20),
            const Text('Disability Information', style: TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Please indicate whether you have any disabilities.', style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 8),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Do you have a disability or impairment?', style: TextStyle(fontSize: 14, color: AppColors.textPrimary)),
              value: _hasDisability,
              onChanged: (v) => setState(() => _hasDisability = v ?? false),
              controlAffinity: ListTileControlAffinity.leading, dense: true,
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildPage4Results() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[1],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Results Details'),
            const SizedBox(height: 16),
            const Text(
              'Please select whether you are applying for a postgraduate or undergraduate qualification.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 20),
            // Matric Year
            TextFormField(
              initialValue: _matricYear == 0 ? null : _matricYear.toString(),
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Matric/Grade 12 Year (YYYY) *',
                prefixIcon: Icon(Icons.calendar_today_outlined),
              ),
              validator: (v) {
                if (v?.trim().isEmpty == true) return 'Required';
                final year = int.tryParse(v!.trim());
                if (year == null) return 'Enter a valid year';
                if (year > DateTime.now().year) return 'Year cannot be in the future';
                return null;
              },
              onChanged: (v) => setState(
                () => _matricYear = int.tryParse(v) ?? 0,
              ),
            ),
            const SizedBox(height: 14),
            // Undergraduate / Postgraduate
            DropdownButtonFormField<String>(
              initialValue:
                  _applicationLevel.isEmpty ? null : _applicationLevel,
              decoration: const InputDecoration(
                labelText: 'Are you applying for Undergraduate or Postgraduate? *',
                prefixIcon: Icon(Icons.school_outlined),
              ),
              items: const [
                DropdownMenuItem(
                  value: '--- Please select ---',
                  child: Text('--- Please select ---'),
                ),
                DropdownMenuItem(
                  value: 'Undergraduate',
                  child: Text('Undergraduate'),
                ),
                DropdownMenuItem(
                  value: 'Postgraduate',
                  child: Text('Postgraduate'),
                ),
              ],
              onChanged: (v) => setState(() => _applicationLevel = v ?? ''),
              validator: (v) =>
                  v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Upgrading
            DropdownButtonFormField<String>(
              initialValue: _isUpgrading.isEmpty ? null : _isUpgrading,
              decoration: const InputDecoration(
                labelText: 'Are you Upgrading? *',
                prefixIcon: Icon(Icons.refresh_outlined),
              ),
              items: const [
                DropdownMenuItem(
                  value: '--- Please select ---',
                  child: Text('--- Please select ---'),
                ),
                DropdownMenuItem(value: 'Yes', child: Text('Yes')),
                DropdownMenuItem(value: 'No', child: Text('No')),
              ],
              onChanged: (v) => setState(() => _isUpgrading = v ?? ''),
              validator: (v) =>
                  v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Matric Type
            DropdownButtonFormField<String>(
              initialValue: _matricType.isEmpty ? null : _matricType,
              decoration: const InputDecoration(
                labelText: 'Matric type *',
                prefixIcon: Icon(Icons.public_outlined),
              ),
              items: const [
                DropdownMenuItem(
                  value: '--- Please select ---',
                  child: Text('--- Please select ---'),
                ),
                DropdownMenuItem(
                  value: 'South African',
                  child: Text('South African'),
                ),
                DropdownMenuItem(
                  value: 'International',
                  child: Text('International'),
                ),
              ],
              onChanged: (v) => setState(() => _matricType = v ?? ''),
              validator: (v) =>
                  v == null || v == '--- Please select ---' ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Examination Number
            TextFormField(
              controller: _examNumberCtrl,
              decoration: const InputDecoration(
                labelText: 'Matric/Grade 12 Examination Number',
                prefixIcon: Icon(Icons.numbers_outlined),
              ),
            ),
            const SizedBox(height: 14),
            // School Leaving Certificate
            TextFormField(
              controller: _schoolLeavingCertCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Final School Leaving Certificate *',
                prefixIcon: Icon(Icons.verified_outlined),
                suffixIcon: Icon(
                  Icons.arrow_drop_down,
                  color: AppColors.textMuted,
                ),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                const certs = [
                  'Cert of Complete Exemption',
                  'GRADE 12',
                  'NTC3/N3/NSC',
                ];
                final result = await _showSearchablePicker(
                  context,
                  title: 'Certificate',
                  options: certs,
                  initialValue: _schoolLeavingCertificate,
                );
                if (result != null) {
                  setState(() => _schoolLeavingCertificate = result);
                }
              },
            ),

            const SizedBox(height: 24),
            const Text(
              'Subject details',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Fill in or select the requested information. Click on the button below to add your subject detail.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _subjectCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'School Leaving Subject',
                prefixIcon: Icon(Icons.book_outlined),
                suffixIcon: Icon(
                  Icons.arrow_drop_down,
                  color: AppColors.textMuted,
                ),
              ),
              onTap: () async {
                final result = await _showSearchablePicker(
                  context,
                  title: 'Subject',
                  options: _schoolSubjects,
                  initialValue: _subjectCtrl.text,
                );
                if (result != null) {
                  setState(() => _subjectCtrl.text = result);
                }
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _gradeCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Grade',
                prefixIcon: Icon(Icons.grade_outlined),
                suffixIcon: Icon(
                  Icons.arrow_drop_down,
                  color: AppColors.textMuted,
                ),
              ),
              onTap: () async {
                const grades = [
                  'NOT ACHIEVED',
                  'ELEMENTARY ACHIEVEMENT',
                  'MODERATE ACHIEVEMENT',
                  'ADEQUATE ACHIEVEMENT',
                  'SUBSTANTIAL ACHIEVEMENT',
                  'MERITORIUS ACHIEVEMENT',
                  'OUTSTANDING ACHIEVEMENT',
                  'NSC',
                ];
                final result = await _showSearchablePicker(
                  context,
                  title: 'Grade',
                  options: grades,
                  initialValue: _gradeCtrl.text,
                );
                if (result != null) {
                  setState(() => _gradeCtrl.text = result);
                }
              },
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              key: ValueKey('subject_result_$_subjectResetKey'),
              initialValue: _subjectResult.isEmpty ? null : _subjectResult,
              decoration: const InputDecoration(
                labelText: 'Result',
                prefixIcon: Icon(Icons.assessment_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Not Achieved', child: Text('Not Achieved')),
                DropdownMenuItem(value: 'Elementary', child: Text('Elementary')),
                DropdownMenuItem(value: 'Moderate', child: Text('Moderate')),
                DropdownMenuItem(value: 'Adequate', child: Text('Adequate')),
                DropdownMenuItem(value: 'Substantial', child: Text('Substantial')),
                DropdownMenuItem(value: 'Meritorius', child: Text('Meritorius')),
                DropdownMenuItem(value: 'Outstanding', child: Text('Outstanding')),
              ],
              onChanged: (v) => setState(() => _subjectResult = v ?? ''),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              key: ValueKey('subject_symbol_$_subjectResetKey'),
              initialValue: _subjectSymbol.isEmpty ? null : _subjectSymbol,
              decoration: const InputDecoration(
                labelText: 'Symbol *',
                prefixIcon: Icon(Icons.grade_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'A', child: Text('A')),
                DropdownMenuItem(value: 'B', child: Text('B')),
                DropdownMenuItem(value: 'C', child: Text('C')),
                DropdownMenuItem(value: 'D', child: Text('D')),
                DropdownMenuItem(value: 'E', child: Text('E')),
                DropdownMenuItem(value: 'F', child: Text('F')),
              ],
              onChanged: (v) => setState(() => _subjectSymbol = v ?? ''),
            ),
            const SizedBox(height: 12),
            // Subject list
            ..._resultsSubjects.asMap().entries.map((entry) {
              final i = entry.key;
              return Card(
                color: AppColors.surfaceLight,
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  dense: true,
                  title: Text(
                    _resultsSubjects[i].subject,
                    style: const TextStyle(fontSize: 13),
                  ),
                  subtitle: Text(
                    'Grade: ${_resultsSubjects[i].grade} | Symbol: ${_resultsSubjects[i].symbol}',
                    style: const TextStyle(fontSize: 11),
                  ),
                  trailing: IconButton(
                    icon: const Icon(
                      Icons.remove_circle_outline,
                      color: AppColors.error,
                      size: 20,
                    ),
                    onPressed: () =>
                        setState(() => _resultsSubjects.removeAt(i)),
                  ),
                ),
              );
            }),
            OutlinedButton.icon(
              onPressed: () {
                final missing = <String>[];
                if (_subjectCtrl.text.trim().isEmpty) missing.add('Subject');
                if (_gradeCtrl.text.trim().isEmpty) missing.add('Grade');
                if (_subjectSymbol.isEmpty) missing.add('Symbol');
                if (missing.isNotEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Please fill in: ${missing.join(', ')}'),
                      duration: const Duration(seconds: 3),
                      backgroundColor: AppColors.error,
                    ),
                  );
                  return;
                }
                setState(() {
                  _resultsSubjects.add(SubjectDetail(
                    subject: _subjectCtrl.text.trim(),
                    grade: _gradeCtrl.text.trim(),
                    result: _subjectResult,
                    symbol: _subjectSymbol,
                  ));
                  _subjectCtrl.clear();
                  _gradeCtrl.clear();
                  _subjectResult = '';
                  _subjectSymbol = '';
                  _subjectResetKey++;
                });
              },
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Add Subject'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.primaryLight,
                side: const BorderSide(color: AppColors.border),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildPage5Qualifications() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[2],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Academic Application'),
            const SizedBox(height: 16),
            const Text(
              'Qualification details',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'The list of qualifications provided can in some cases only be the qualifications you qualify for.\n\n'
              'If you have written a South African matric we will take the subjects and marks on the Matric page as the guide to determine for which qualifications you qualify.\n\n'
              'If you have not written a South African matric or if you are applying for a post-graduate qualification the list will be exhaustive.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
            ),
            const SizedBox(height: 20),

            // Academic Year
            DropdownButtonFormField<String>(
              initialValue: _academicYear == 0 ? null : _academicYear.toString(),
              decoration: const InputDecoration(
                labelText: 'Academic Year *',
                prefixIcon: Icon(Icons.calendar_today_outlined),
              ),
              items: List.generate(10, (i) {
                final year = DateTime.now().year + i;
                return DropdownMenuItem(
                  value: year.toString(),
                  child: Text(year.toString()),
                );
              }),
              onChanged: (v) => setState(() => _academicYear = int.tryParse(v ?? '0') ?? 0),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),

            // Faculty
            TextFormField(
              controller: _facultyCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Limit your selection to a specific Faculty/School *',
                prefixIcon: Icon(Icons.account_balance_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await _showSearchablePicker(
                  context,
                  title: 'Faculty',
                  options: const [
                    'HEALTH SCIENCES',
                    'HUMANITIES, SOCIAL SCIENCES AND EDUCATION',
                    'MANAGEMENT, COMMERCE AND LAW',
                    'SCIENCE, ENGINEERING AND AGRICULTURE',
                  ],
                  initialValue: _facultyCtrl.text,
                );
                if (result != null) {
                  setState(() => _facultyCtrl.text = result);
                }
              },
            ),
            const SizedBox(height: 14),

            // Programme
            TextFormField(
              controller: _programmeCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Choose a programme *',
                prefixIcon: Icon(Icons.school_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await _showSearchablePicker(
                  context,
                  title: 'Programme',
                  options: const ['HSBAMS - BA (MEDIA STUDIES)', 'HSBADS - BA IN DEVELOPMENT STUDIES', 'HSBAIR - BA IN INTERNATIONAL RELATIONS'],
                  initialValue: _programmeCtrl.text,
                );
                if (result != null) {
                  setState(() => _programmeCtrl.text = result);
                }
              },
            ),
            const SizedBox(height: 14),

            // Application Period
            TextFormField(
              controller: TextEditingController(text: _applicationPeriod.isEmpty ? null : _applicationPeriod),
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'For which period are you applying? *',
                prefixIcon: Icon(Icons.date_range_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await _showSearchablePicker(
                  context,
                  title: 'Period',
                  options: const ['YEAR', 'SEMESTER 1', 'SEMESTER 2'],
                  initialValue: _applicationPeriod,
                );
                if (result != null) {
                  setState(() => _applicationPeriod = result);
                }
              },
            ),
            const SizedBox(height: 14),

            // Study Mode
            TextFormField(
              controller: TextEditingController(text: _studyMode.isEmpty ? null : _studyMode),
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'How would you like to study for this programme? *',
                prefixIcon: Icon(Icons.school_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await _showSearchablePicker(
                  context,
                  title: 'Study Mode',
                  options: const ['FULL-TIME', 'PART-TIME', 'DISTANCE'],
                  initialValue: _studyMode,
                );
                if (result != null) {
                  setState(() => _studyMode = result);
                }
              },
            ),
            const SizedBox(height: 14),

            // Study Timing
            TextFormField(
              controller: TextEditingController(text: _studyTiming.isEmpty ? null : _studyTiming),
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'When would you like to study for the qualification? *',
                prefixIcon: Icon(Icons.access_time_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await _showSearchablePicker(
                  context,
                  title: 'Study Timing',
                  options: const ['YEAR'],
                  initialValue: _studyTiming,
                );
                if (result != null) {
                  setState(() => _studyTiming = result);
                }
              },
            ),
            const SizedBox(height: 24),

            // Application Type (read-only display)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surfaceLight,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Application Type',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'AT: $_applicationType',
                    style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
                  ),
                  Text(
                    _applicationTypeDesc,
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                  ),
                  Text(
                    'Number of applications allowed for this Application type: $_numAppsAllowed',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Add Qualification button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _addQualification,
                icon: const Icon(Icons.add),
                label: const Text('Add Qualification'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),

            // Qualification list
            if (_qualificationChoices.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text(
                'Added Qualifications',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              ..._qualificationChoices.asMap().entries.map((entry) {
                final i = entry.key;
                final q = entry.value;
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(q.programme, style: const TextStyle(fontSize: 13)),
                    subtitle: Text(q.faculty, style: const TextStyle(fontSize: 11)),
                    trailing: IconButton(
                      icon: const Icon(Icons.remove_circle_outline, color: AppColors.error, size: 20),
                      onPressed: () => setState(() => _qualificationChoices.removeAt(i)),
                    ),
                  ),
                );
              }),
            ],
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  void _addQualification() {
    final faculty = _facultyCtrl.text.trim();
    final programme = _programmeCtrl.text.trim();
    if (faculty.isEmpty || programme.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a faculty and programme first'),
          backgroundColor: AppColors.error,
        ),
      );
      return;
    }
    setState(() {
      _qualificationChoices.add(QualificationChoice(faculty: faculty, programme: programme));
      _facultyCtrl.clear();
      _programmeCtrl.clear();
    });
  }

  Future<void> _saveCurrentPage() async {
    setState(() => _saving = true);
    try {
      final authState = ref.read(authProvider);
      final existingProfile = authState.value?.profile;
      final id = existingProfile?.id ?? const Uuid().v4();

      final profile = StudentProfile(
        id: id,
        personal: PersonalDetails(
          title: _title,
          initials: _initialsCtrl.text.trim(),
          firstName: _firstNamesCtrl.text.trim(),
          lastName: _surnameCtrl.text.trim(),
          maidenName: _maidenNameCtrl.text.trim(),
          gender: _gender,
          dateOfBirth: _selectedDob,
          idNumber: _idNumberCtrl.text.trim(),
        ),
        contact: ContactInfo(
          email: _emailCtrl.text.trim(),
          phone: _homePhoneCtrl.text.trim(),
          workPhone: _workPhoneCtrl.text.trim(),
          hasSACellphone: _hasSACellphone,
          verifyEmail: _verifyEmailCtrl.text.trim(),
        ),
        address: AddressInfo(
          address: _streetAddr1Ctrl.text.trim(),
          addressLine2: _streetAddr2Ctrl.text.trim(),
          addressLine3: _streetAddr3Ctrl.text.trim(),
          province: _streetProvince,
          postalCode: _streetPostalCodeCtrl.text.trim(),
          postalAddress: _postalDifferent
              ? _postalAddr1Ctrl.text.trim()
              : _streetAddr1Ctrl.text.trim(),
        ),
        demographic: DemographicInfo(
          nationality: _isSACitizen,
          homeLanguage: _homeLanguageCtrl.text.trim(),
          populationGroup: _ethnicGroup,
          maritalStatus: _maritalStatus,
          citizenshipCode: _citizenshipCodeCtrl.text.trim(),
          heardAboutUs: _heardAboutUsCtrl.text.trim(),
        ),
        status: StatusInfo(
          disabilityStatus: _hasDisability ? 'Yes' : 'No',
          bursaryRequired: _bursaryRequired,
          employmentStatus: _isEmployed,
          wantsResidence: _wantsResidence,
        ),
        qualification: QualificationInfo(
          academicYear: _academicYear,
          choices: _qualificationChoices,
          applicationPeriod: _applicationPeriod,
          studyMode: _studyMode,
          studyTiming: _studyTiming,
          applicationType: _applicationType,
          applicationTypeDescription: _applicationTypeDesc,
          numApplicationsAllowed: _numAppsAllowed,
        ),
        nextOfKin: NextOfKin(
          name: _nextOfKinNameCtrl.text.trim(),
          mobilePhone: _nextOfKinMobileCtrl.text.trim(),
          homePhone: _nextOfKinHomePhoneCtrl.text.trim(),
          workPhone: _nextOfKinWorkPhoneCtrl.text.trim(),
          addressLine1: _nextOfKinAddr1Ctrl.text.trim(),
          addressLine2: _nextOfKinAddr2Ctrl.text.trim(),
          addressLine3: _nextOfKinAddr3Ctrl.text.trim(),
          addressLine4: _nextOfKinAddr4Ctrl.text.trim(),
          postalCode: _nextOfKinPostalCodeCtrl.text.trim(),
          email: _nextOfKinEmailCtrl.text.trim(),
        ),
        accountContact: AccountContact(
          name: _accountContactNameCtrl.text.trim(),
          mobilePhone: _accountContactMobileCtrl.text.trim(),
          homePhone: _accountContactHomePhoneCtrl.text.trim(),
          addressLine1: _accountContactAddr1Ctrl.text.trim(),
          addressLine2: _accountContactAddr2Ctrl.text.trim(),
          addressLine3: _accountContactAddr3Ctrl.text.trim(),
          addressLine4: _accountContactAddr4Ctrl.text.trim(),
          postalCode: _accountContactPostalCodeCtrl.text.trim(),
          email: _accountContactEmailCtrl.text.trim(),
        ),
        results: ResultsInfo(
          matricYear: _matricYear,
          applicationLevel: _applicationLevel,
          upgrading: _isUpgrading,
          matricType: _matricType,
          examinationNumber: _examNumberCtrl.text.trim(),
          schoolLeavingCertificate: _schoolLeavingCertificate,
          subjects: _resultsSubjects,
        ),
        onboardingComplete: existingProfile?.onboardingComplete ?? false,
      );

      await ref.read(profileProvider.notifier).saveProfile(profile);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Progress saved!'),
            duration: Duration(seconds: 1),
            backgroundColor: AppColors.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Save failed: $e'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
    if (mounted) {
      setState(() => _saving = false);
    }
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
          if (_currentPage > 0) const SizedBox(width: 8),
          Expanded(
            child: OutlinedButton(
              onPressed: _saving ? null : _saveCurrentPage,
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppColors.primary),
              ),
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppColors.primary,
                      ),
                    )
                  : const Text('Save'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: ElevatedButton(
              onPressed: _saving ? null : _saveAndContinue,
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(_currentPage < 2 ? 'Next' : 'Finish'),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        color: AppColors.textPrimary,
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
    );
  }
}
