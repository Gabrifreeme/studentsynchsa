import 'dart:async';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

class AppWebView extends StatefulWidget {
  final String url;
  final String universityName;
  const AppWebView({super.key, required this.url, required this.universityName});

  @override
  State<AppWebView> createState() => _AppWebViewState();
}

class _AppWebViewState extends State<AppWebView> {
  late final WebViewController _controller;
  bool _loading = true;
  Timer? _injectTimer;
  String _profileJson = '{}';

  @override
  void initState() {
    super.initState();
    _loadProfileOnce();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) {
          setState(() => _loading = true);
        },
        onPageFinished: (_) {
          setState(() => _loading = false);
          _injectStar();
          Future.delayed(const Duration(seconds: 1), _injectStar);
          Future.delayed(const Duration(seconds: 3), _injectStar);
        },
      ))
      ..loadRequest(Uri.parse(widget.url));
    _injectTimer = Timer.periodic(const Duration(seconds: 3), (_) => _injectStar());
  }

  Future<void> _loadProfileOnce() async {
    final repo = ProfileRepositoryImpl();
    var profile = await repo.getProfile();
    if (profile == null) {
      await Future.delayed(const Duration(seconds: 1));
      profile = await repo.getProfile();
    }
    if (profile == null) {
      await Future.delayed(const Duration(seconds: 2));
      profile = await repo.getProfile();
    }
    if (profile != null && mounted) {
      _profileJson = _profileToSimpleJson(profile);
      _injectStar();
    }
  }

  @override
  void dispose() {
    _injectTimer?.cancel();
    super.dispose();
  }

  Future<void> _injectStar() async {
    try {
      await _controller.runJavaScript(star.buildAutofillScript(_profileJson));
    } catch (_) {}
  }

  Future<void> _autofillNow() async {
    try {
      await _controller.runJavaScript(star.buildAutofillOnlyScript(_profileJson));
    } catch (_) {}
  }

  String _profileToSimpleJson(StudentProfile p) {
    String e(String s) => s.replaceAll('\\', '\\\\').replaceAll('"', '\\"').replaceAll('\n', '\\n');
    return '''
{
  "personal": {
    "title": "${e(p.personal.title)}",
    "firstName": "${e(p.personal.firstName)}",
    "lastName": "${e(p.personal.lastName)}",
    "initials": "${e(p.personal.initials)}",
    "gender": "${e(p.personal.gender)}",
    "dateOfBirth": "${p.personal.dateOfBirth?.toIso8601String().split('T').first ?? ''}",
    "idNumber": "${e(p.personal.idNumber)}"
  },
  "contact": {
    "email": "${e(p.contact.email)}",
    "phone": "${e(p.contact.phone)}",
    "workPhone": "${e(p.contact.workPhone)}"
  },
  "address": {
    "address": "${e(p.address.address)}",
    "addressLine2": "${e(p.address.addressLine2)}",
    "province": "${e(p.address.province)}",
    "postalCode": "${e(p.address.postalCode)}"
  },
  "demographic": {
    "nationality": "${e(p.demographic.nationality)}",
    "citizenship": "${e(p.demographic.nationality)}",
    "homeLanguage": "${e(p.demographic.homeLanguage)}",
    "populationGroup": "${e(p.demographic.populationGroup)}",
    "maritalStatus": "${e(p.demographic.maritalStatus)}"
  },
  "school": {
    "schoolName": "${e(p.school.schoolName)}",
    "currentGrade": "${e(p.school.currentGrade)}"
  },
  "results": {
    "matricYear": ${p.results.matricYear},
    "matricType": "${e(p.results.matricType)}",
    "examinationNumber": "${e(p.results.examinationNumber)}",
    "applicationLevel": "${e(p.results.applicationLevel)}"
  },
  "nextOfKin": {
    "name": "${e(p.nextOfKin.name)}",
    "mobilePhone": "${e(p.nextOfKin.mobilePhone)}",
    "email": "${e(p.nextOfKin.email)}"
  },
  "qualification": {
    "academicYear": ${p.qualification.academicYear},
    "studyMode": "${e(p.qualification.studyMode)}",
    "choices": [
      {
        "faculty": "${e(p.qualification.choices.isNotEmpty ? p.qualification.choices.first.faculty : '')}",
        "programme": "${e(p.qualification.choices.isNotEmpty ? p.qualification.choices.first.programme : '')}"
      }
    ]
  }
}''';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: AppColors.surface,
        actions: [
          IconButton(
            icon: const Icon(Icons.star_rounded, color: Color(0xFFFFD700)),
            tooltip: 'Star Auto-Fill',
            onPressed: () => _autofillNow(),
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_loading)
            const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
