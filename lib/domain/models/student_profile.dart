class PersonalDetails {
  final String title;
  final String initials;
  final String firstName;
  final String lastName;
  final String maidenName;
  final String gender;
  final DateTime? dateOfBirth;
  final String idNumber;

  const PersonalDetails({
    this.title = '',
    this.initials = '',
    this.firstName = '',
    this.lastName = '',
    this.maidenName = '',
    this.gender = '',
    this.dateOfBirth,
    this.idNumber = '',
  });

  PersonalDetails copyWith({
    String? title,
    String? initials,
    String? firstName,
    String? lastName,
    String? maidenName,
    String? gender,
    DateTime? dateOfBirth,
    String? idNumber,
  }) =>
      PersonalDetails(
        title: title ?? this.title,
        initials: initials ?? this.initials,
        firstName: firstName ?? this.firstName,
        lastName: lastName ?? this.lastName,
        maidenName: maidenName ?? this.maidenName,
        gender: gender ?? this.gender,
        dateOfBirth: dateOfBirth ?? this.dateOfBirth,
        idNumber: idNumber ?? this.idNumber,
      );

  Map<String, dynamic> toJson() => {
    'title': title,
    'initials': initials,
    'firstName': firstName,
    'lastName': lastName,
    'maidenName': maidenName,
    'gender': gender,
    'dateOfBirth': dateOfBirth?.toIso8601String(),
    'idNumber': idNumber,
  };

  factory PersonalDetails.fromJson(Map<String, dynamic> json) => PersonalDetails(
    title: json['title'] ?? '',
    initials: json['initials'] ?? '',
    firstName: json['firstName'] ?? '',
    lastName: json['lastName'] ?? '',
    maidenName: json['maidenName'] ?? '',
    gender: json['gender'] ?? '',
    dateOfBirth: json['dateOfBirth'] != null ? DateTime.tryParse(json['dateOfBirth']) : null,
    idNumber: json['idNumber'] ?? '',
  );
}

class ContactInfo {
  final String email;
  final String phone;
  final String workPhone;

  const ContactInfo({this.email = '', this.phone = '', this.workPhone = ''});

  ContactInfo copyWith({String? email, String? phone, String? workPhone}) =>
      ContactInfo(email: email ?? this.email, phone: phone ?? this.phone, workPhone: workPhone ?? this.workPhone);

  Map<String, dynamic> toJson() => {'email': email, 'phone': phone, 'workPhone': workPhone};

  factory ContactInfo.fromJson(Map<String, dynamic> json) => ContactInfo(
    email: json['email'] ?? '',
    phone: json['phone'] ?? '',
    workPhone: json['workPhone'] ?? '',
  );
}

class AddressInfo {
  final String address;
  final String addressLine2;
  final String addressLine3;
  final String province;
  final String postalCode;
  final String postalAddress;

  const AddressInfo({
    this.address = '',
    this.addressLine2 = '',
    this.addressLine3 = '',
    this.province = '',
    this.postalCode = '',
    this.postalAddress = '',
  });

  AddressInfo copyWith({
    String? address,
    String? addressLine2,
    String? addressLine3,
    String? province,
    String? postalCode,
    String? postalAddress,
  }) =>
      AddressInfo(
        address: address ?? this.address,
        addressLine2: addressLine2 ?? this.addressLine2,
        addressLine3: addressLine3 ?? this.addressLine3,
        province: province ?? this.province,
        postalCode: postalCode ?? this.postalCode,
        postalAddress: postalAddress ?? this.postalAddress,
      );

  Map<String, dynamic> toJson() => {
    'address': address,
    'addressLine2': addressLine2,
    'addressLine3': addressLine3,
    'province': province,
    'postalCode': postalCode,
    'postalAddress': postalAddress,
  };

  factory AddressInfo.fromJson(Map<String, dynamic> json) => AddressInfo(
    address: json['address'] ?? '',
    addressLine2: json['addressLine2'] ?? '',
    addressLine3: json['addressLine3'] ?? '',
    province: json['province'] ?? '',
    postalCode: json['postalCode'] ?? '',
    postalAddress: json['postalAddress'] ?? '',
  );
}

class DemographicInfo {
  final String nationality;
  final String countryOfBirth;
  final String homeLanguage;
  final String populationGroup;
  final String maritalStatus;

  const DemographicInfo({
    this.nationality = 'South African',
    this.countryOfBirth = '',
    this.homeLanguage = '',
    this.populationGroup = '',
    this.maritalStatus = '',
  });

  DemographicInfo copyWith({
    String? nationality,
    String? countryOfBirth,
    String? homeLanguage,
    String? populationGroup,
    String? maritalStatus,
  }) =>
      DemographicInfo(
        nationality: nationality ?? this.nationality,
        countryOfBirth: countryOfBirth ?? this.countryOfBirth,
        homeLanguage: homeLanguage ?? this.homeLanguage,
        populationGroup: populationGroup ?? this.populationGroup,
        maritalStatus: maritalStatus ?? this.maritalStatus,
      );

  Map<String, dynamic> toJson() => {
    'nationality': nationality,
    'countryOfBirth': countryOfBirth,
    'homeLanguage': homeLanguage,
    'populationGroup': populationGroup,
    'maritalStatus': maritalStatus,
  };

  factory DemographicInfo.fromJson(Map<String, dynamic> json) => DemographicInfo(
    nationality: json['nationality'] ?? 'South African',
    countryOfBirth: json['countryOfBirth'] ?? '',
    homeLanguage: json['homeLanguage'] ?? '',
    populationGroup: json['populationGroup'] ?? '',
    maritalStatus: json['maritalStatus'] ?? '',
  );
}

class StatusInfo {
  final String disabilityStatus;
  final String bursaryRequired;
  final String employmentStatus;

  const StatusInfo({this.disabilityStatus = '', this.bursaryRequired = '', this.employmentStatus = ''});

  StatusInfo copyWith({String? disabilityStatus, String? bursaryRequired, String? employmentStatus}) =>
      StatusInfo(
        disabilityStatus: disabilityStatus ?? this.disabilityStatus,
        bursaryRequired: bursaryRequired ?? this.bursaryRequired,
        employmentStatus: employmentStatus ?? this.employmentStatus,
      );

  Map<String, dynamic> toJson() => {
    'disabilityStatus': disabilityStatus,
    'bursaryRequired': bursaryRequired,
    'employmentStatus': employmentStatus,
  };

  factory StatusInfo.fromJson(Map<String, dynamic> json) => StatusInfo(
    disabilityStatus: json['disabilityStatus'] ?? '',
    bursaryRequired: json['bursaryRequired'] ?? '',
    employmentStatus: json['employmentStatus'] ?? '',
  );
}

class SchoolInfo {
  final String schoolName;
  final String currentGrade;
  final String yearOfMatric;
  final String currentlyDoing;
  final String studiedPreviously;

  const SchoolInfo({this.schoolName = '', this.currentGrade = '', this.yearOfMatric = '', this.currentlyDoing = '', this.studiedPreviously = ''});

  SchoolInfo copyWith({String? schoolName, String? currentGrade, String? yearOfMatric, String? currentlyDoing, String? studiedPreviously}) =>
      SchoolInfo(
        schoolName: schoolName ?? this.schoolName,
        currentGrade: currentGrade ?? this.currentGrade,
        yearOfMatric: yearOfMatric ?? this.yearOfMatric,
        currentlyDoing: currentlyDoing ?? this.currentlyDoing,
        studiedPreviously: studiedPreviously ?? this.studiedPreviously,
      );

  Map<String, dynamic> toJson() => {'schoolName': schoolName, 'currentGrade': currentGrade, 'yearOfMatric': yearOfMatric, 'currentlyDoing': currentlyDoing, 'studiedPreviously': studiedPreviously};

  factory SchoolInfo.fromJson(Map<String, dynamic> json) => SchoolInfo(
    schoolName: json['schoolName'] ?? '',
    currentGrade: json['currentGrade'] ?? '',
    yearOfMatric: json['yearOfMatric'] ?? '',
    currentlyDoing: json['currentlyDoing'] ?? '',
    studiedPreviously: json['studiedPreviously'] ?? '',
  );
}

class NextOfKin {
  final String name;
  final String mobilePhone;
  final String homePhone;
  final String workPhone;
  final String addressLine1;
  final String addressLine2;
  final String addressLine3;
  final String addressLine4;
  final String postalCode;
  final String email;

  const NextOfKin({
    this.name = '',
    this.mobilePhone = '',
    this.homePhone = '',
    this.workPhone = '',
    this.addressLine1 = '',
    this.addressLine2 = '',
    this.addressLine3 = '',
    this.addressLine4 = '',
    this.postalCode = '',
    this.email = '',
  });

  NextOfKin copyWith({
    String? name,
    String? mobilePhone,
    String? homePhone,
    String? workPhone,
    String? addressLine1,
    String? addressLine2,
    String? addressLine3,
    String? addressLine4,
    String? postalCode,
    String? email,
  }) =>
      NextOfKin(
        name: name ?? this.name,
        mobilePhone: mobilePhone ?? this.mobilePhone,
        homePhone: homePhone ?? this.homePhone,
        workPhone: workPhone ?? this.workPhone,
        addressLine1: addressLine1 ?? this.addressLine1,
        addressLine2: addressLine2 ?? this.addressLine2,
        addressLine3: addressLine3 ?? this.addressLine3,
        addressLine4: addressLine4 ?? this.addressLine4,
        postalCode: postalCode ?? this.postalCode,
        email: email ?? this.email,
      );

  Map<String, dynamic> toJson() => {
    'name': name,
    'mobilePhone': mobilePhone,
    'homePhone': homePhone,
    'workPhone': workPhone,
    'addressLine1': addressLine1,
    'addressLine2': addressLine2,
    'addressLine3': addressLine3,
    'addressLine4': addressLine4,
    'postalCode': postalCode,
    'email': email,
  };

  factory NextOfKin.fromJson(Map<String, dynamic> json) => NextOfKin(
    name: json['name'] ?? '',
    mobilePhone: json['mobilePhone'] ?? '',
    homePhone: json['homePhone'] ?? '',
    workPhone: json['workPhone'] ?? '',
    addressLine1: json['addressLine1'] ?? '',
    addressLine2: json['addressLine2'] ?? '',
    addressLine3: json['addressLine3'] ?? '',
    addressLine4: json['addressLine4'] ?? '',
    postalCode: json['postalCode'] ?? '',
    email: json['email'] ?? '',
  );
}

class AccountContact {
  final String name;
  final String mobilePhone;
  final String homePhone;
  final String addressLine1;
  final String addressLine2;
  final String addressLine3;
  final String addressLine4;
  final String postalCode;
  final String email;

  const AccountContact({
    this.name = '',
    this.mobilePhone = '',
    this.homePhone = '',
    this.addressLine1 = '',
    this.addressLine2 = '',
    this.addressLine3 = '',
    this.addressLine4 = '',
    this.postalCode = '',
    this.email = '',
  });

  AccountContact copyWith({
    String? name,
    String? mobilePhone,
    String? homePhone,
    String? addressLine1,
    String? addressLine2,
    String? addressLine3,
    String? addressLine4,
    String? postalCode,
    String? email,
  }) =>
      AccountContact(
        name: name ?? this.name,
        mobilePhone: mobilePhone ?? this.mobilePhone,
        homePhone: homePhone ?? this.homePhone,
        addressLine1: addressLine1 ?? this.addressLine1,
        addressLine2: addressLine2 ?? this.addressLine2,
        addressLine3: addressLine3 ?? this.addressLine3,
        addressLine4: addressLine4 ?? this.addressLine4,
        postalCode: postalCode ?? this.postalCode,
        email: email ?? this.email,
      );

  Map<String, dynamic> toJson() => {
    'name': name,
    'mobilePhone': mobilePhone,
    'homePhone': homePhone,
    'addressLine1': addressLine1,
    'addressLine2': addressLine2,
    'addressLine3': addressLine3,
    'addressLine4': addressLine4,
    'postalCode': postalCode,
    'email': email,
  };

  factory AccountContact.fromJson(Map<String, dynamic> json) => AccountContact(
    name: json['name'] ?? '',
    mobilePhone: json['mobilePhone'] ?? '',
    homePhone: json['homePhone'] ?? '',
    addressLine1: json['addressLine1'] ?? '',
    addressLine2: json['addressLine2'] ?? '',
    addressLine3: json['addressLine3'] ?? '',
    addressLine4: json['addressLine4'] ?? '',
    postalCode: json['postalCode'] ?? '',
    email: json['email'] ?? '',
  );
}

class SubjectDetail {
  final String subject;
  final String grade;
  final String result;
  final String symbol;

  const SubjectDetail({this.subject = '', this.grade = '', this.result = '', this.symbol = ''});

  SubjectDetail copyWith({String? subject, String? grade, String? result, String? symbol}) =>
      SubjectDetail(
        subject: subject ?? this.subject,
        grade: grade ?? this.grade,
        result: result ?? this.result,
        symbol: symbol ?? this.symbol,
      );

  Map<String, dynamic> toJson() => {'subject': subject, 'grade': grade, 'result': result, 'symbol': symbol};

  factory SubjectDetail.fromJson(Map<String, dynamic> json) => SubjectDetail(
    subject: json['subject'] ?? '',
    grade: json['grade'] ?? '',
    result: json['result'] ?? '',
    symbol: json['symbol'] ?? '',
  );
}

class ResultsInfo {
  final int matricYear;
  final String applicationLevel;
  final String upgrading;
  final String matricType;
  final String examinationNumber;
  final String schoolLeavingCertificate;
  final List<SubjectDetail> subjects;

  const ResultsInfo({
    this.matricYear = 0,
    this.applicationLevel = '',
    this.upgrading = '',
    this.matricType = '',
    this.examinationNumber = '',
    this.schoolLeavingCertificate = '',
    this.subjects = const [],
  });

  ResultsInfo copyWith({
    int? matricYear,
    String? applicationLevel,
    String? upgrading,
    String? matricType,
    String? examinationNumber,
    String? schoolLeavingCertificate,
    List<SubjectDetail>? subjects,
  }) =>
      ResultsInfo(
        matricYear: matricYear ?? this.matricYear,
        applicationLevel: applicationLevel ?? this.applicationLevel,
        upgrading: upgrading ?? this.upgrading,
        matricType: matricType ?? this.matricType,
        examinationNumber: examinationNumber ?? this.examinationNumber,
        schoolLeavingCertificate: schoolLeavingCertificate ?? this.schoolLeavingCertificate,
        subjects: subjects ?? this.subjects,
      );

  Map<String, dynamic> toJson() => {
    'matricYear': matricYear,
    'applicationLevel': applicationLevel,
    'upgrading': upgrading,
    'matricType': matricType,
    'examinationNumber': examinationNumber,
    'schoolLeavingCertificate': schoolLeavingCertificate,
    'subjects': subjects.map((s) => s.toJson()).toList(),
  };

  factory ResultsInfo.fromJson(Map<String, dynamic> json) => ResultsInfo(
    matricYear: json['matricYear'] ?? 0,
    applicationLevel: json['applicationLevel'] ?? '',
    upgrading: json['upgrading'] ?? '',
    matricType: json['matricType'] ?? '',
    examinationNumber: json['examinationNumber'] ?? '',
    schoolLeavingCertificate: json['schoolLeavingCertificate'] ?? '',
    subjects: (json['subjects'] as List?)?.map((s) => SubjectDetail.fromJson(s)).toList() ?? [],
  );
}

class QualificationChoice {
  final String faculty;
  final String programme;

  const QualificationChoice({this.faculty = '', this.programme = ''});

  QualificationChoice copyWith({String? faculty, String? programme}) =>
      QualificationChoice(faculty: faculty ?? this.faculty, programme: programme ?? this.programme);

  Map<String, dynamic> toJson() => {'faculty': faculty, 'programme': programme};

  factory QualificationChoice.fromJson(Map<String, dynamic> json) => QualificationChoice(
    faculty: json['faculty'] ?? '',
    programme: json['programme'] ?? '',
  );
}

class QualificationInfo {
  final int academicYear;
  final List<QualificationChoice> choices;
  final String applicationPeriod;
  final String studyMode;
  final String studyTiming;

  const QualificationInfo({
    this.academicYear = 0,
    this.choices = const [],
    this.applicationPeriod = '',
    this.studyMode = '',
    this.studyTiming = '',
  });

  QualificationInfo copyWith({
    int? academicYear,
    List<QualificationChoice>? choices,
    String? applicationPeriod,
    String? studyMode,
    String? studyTiming,
  }) =>
      QualificationInfo(
        academicYear: academicYear ?? this.academicYear,
        choices: choices ?? this.choices,
        applicationPeriod: applicationPeriod ?? this.applicationPeriod,
        studyMode: studyMode ?? this.studyMode,
        studyTiming: studyTiming ?? this.studyTiming,
      );

  Map<String, dynamic> toJson() => {
    'academicYear': academicYear,
    'choices': choices.map((c) => c.toJson()).toList(),
    'applicationPeriod': applicationPeriod,
    'studyMode': studyMode,
    'studyTiming': studyTiming,
  };

  factory QualificationInfo.fromJson(Map<String, dynamic> json) => QualificationInfo(
    academicYear: json['academicYear'] ?? 0,
    choices: (json['choices'] as List?)?.map((c) => QualificationChoice.fromJson(c)).toList() ?? [],
    applicationPeriod: json['applicationPeriod'] ?? '',
    studyMode: json['studyMode'] ?? '',
    studyTiming: json['studyTiming'] ?? '',
  );
}

class AgreementInfo {
  final String loginPin;
  final String acceptanceStatus;

  const AgreementInfo({this.loginPin = '', this.acceptanceStatus = ''});

  AgreementInfo copyWith({String? loginPin, String? acceptanceStatus}) =>
      AgreementInfo(
        loginPin: loginPin ?? this.loginPin,
        acceptanceStatus: acceptanceStatus ?? this.acceptanceStatus,
      );

  Map<String, dynamic> toJson() => {'loginPin': loginPin, 'acceptanceStatus': acceptanceStatus};

  factory AgreementInfo.fromJson(Map<String, dynamic> json) => AgreementInfo(
    loginPin: json['loginPin'] ?? '',
    acceptanceStatus: json['acceptanceStatus'] ?? '',
  );
}

class StudentProfile {
  final String id;
  final PersonalDetails personal;
  final ContactInfo contact;
  final AddressInfo address;
  final DemographicInfo demographic;
  final StatusInfo status;
  final SchoolInfo school;
  final NextOfKin nextOfKin;
  final AccountContact accountContact;
  final ResultsInfo results;
  final QualificationInfo qualification;
  final AgreementInfo agreement;
  final List<String> uploadedDocuments;
  final List<SubjectMark> grade11Subjects;
  final List<SubjectMark> grade12Subjects;
  final List<String> preferredUniversities;
  final List<String> preferredCourses;
  final List<String> careerInterests;
  final bool onboardingComplete;
  final DateTime createdAt;
  final DateTime updatedAt;

  StudentProfile({
    required this.id,
    PersonalDetails? personal,
    ContactInfo? contact,
    AddressInfo? address,
    DemographicInfo? demographic,
    StatusInfo? status,
    SchoolInfo? school,
    NextOfKin? nextOfKin,
    AccountContact? accountContact,
    ResultsInfo? results,
    QualificationInfo? qualification,
    AgreementInfo? agreement,
    this.uploadedDocuments = const [],
    this.grade11Subjects = const [],
    this.grade12Subjects = const [],
    this.preferredUniversities = const [],
    this.preferredCourses = const [],
    this.careerInterests = const [],
    this.onboardingComplete = false,
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : personal = personal ?? const PersonalDetails(),
        contact = contact ?? const ContactInfo(),
        address = address ?? const AddressInfo(),
        demographic = demographic ?? const DemographicInfo(),
        status = status ?? const StatusInfo(),
        school = school ?? const SchoolInfo(),
        nextOfKin = nextOfKin ?? const NextOfKin(),
        accountContact = accountContact ?? const AccountContact(),
        results = results ?? const ResultsInfo(),
        qualification = qualification ?? const QualificationInfo(),
        agreement = agreement ?? const AgreementInfo(),
        createdAt = createdAt ?? DateTime.now(),
        updatedAt = updatedAt ?? DateTime.now();

  int get apsScore => _calculateAps(grade12Subjects.isNotEmpty ? grade12Subjects : grade11Subjects);

  int _calculateAps(List<SubjectMark> subjects) {
    if (subjects.isEmpty) return 0;
    int total = 0;
    for (final s in subjects) {
      total += _percentageToAps(s.mark);
    }
    return total;
  }

  int _percentageToAps(double percentage) {
    if (percentage >= 80) return 7;
    if (percentage >= 70) return 6;
    if (percentage >= 60) return 5;
    if (percentage >= 50) return 4;
    if (percentage >= 40) return 3;
    if (percentage >= 30) return 2;
    return 1;
  }

  StudentProfile copyWith({
    PersonalDetails? personal,
    ContactInfo? contact,
    AddressInfo? address,
    DemographicInfo? demographic,
    StatusInfo? status,
    SchoolInfo? school,
    NextOfKin? nextOfKin,
    AccountContact? accountContact,
    ResultsInfo? results,
    QualificationInfo? qualification,
    AgreementInfo? agreement,
    List<String>? uploadedDocuments,
    List<SubjectMark>? grade11Subjects,
    List<SubjectMark>? grade12Subjects,
    List<String>? preferredUniversities,
    List<String>? preferredCourses,
    List<String>? careerInterests,
    bool? onboardingComplete,
  }) =>
      StudentProfile(
        id: id,
        personal: this.personal.copyWith(
          title: personal?.title,
          initials: personal?.initials,
          firstName: personal?.firstName,
          lastName: personal?.lastName,
          maidenName: personal?.maidenName,
          gender: personal?.gender,
          dateOfBirth: personal?.dateOfBirth,
          idNumber: personal?.idNumber,
        ),
        contact: this.contact.copyWith(
          email: contact?.email,
          phone: contact?.phone,
          workPhone: contact?.workPhone,
        ),
        address: this.address.copyWith(
          address: address?.address,
          addressLine2: address?.addressLine2,
          addressLine3: address?.addressLine3,
          province: address?.province,
          postalCode: address?.postalCode,
          postalAddress: address?.postalAddress,
        ),
        demographic: this.demographic.copyWith(
          nationality: demographic?.nationality,
          countryOfBirth: demographic?.countryOfBirth,
          homeLanguage: demographic?.homeLanguage,
          populationGroup: demographic?.populationGroup,
          maritalStatus: demographic?.maritalStatus,
        ),
        status: this.status.copyWith(
          disabilityStatus: status?.disabilityStatus,
          bursaryRequired: status?.bursaryRequired,
          employmentStatus: status?.employmentStatus,
        ),
        school: this.school.copyWith(
          schoolName: school?.schoolName,
          currentGrade: school?.currentGrade,
          yearOfMatric: school?.yearOfMatric,
          currentlyDoing: school?.currentlyDoing,
          studiedPreviously: school?.studiedPreviously,
        ),
        grade11Subjects: grade11Subjects ?? this.grade11Subjects,
        grade12Subjects: grade12Subjects ?? this.grade12Subjects,
        preferredUniversities: preferredUniversities ?? this.preferredUniversities,
        preferredCourses: preferredCourses ?? this.preferredCourses,
        careerInterests: careerInterests ?? this.careerInterests,
        nextOfKin: nextOfKin ?? this.nextOfKin,
        accountContact: accountContact ?? this.accountContact,
        results: results ?? this.results,
        qualification: qualification ?? this.qualification,
        agreement: agreement ?? this.agreement,
        uploadedDocuments: uploadedDocuments ?? this.uploadedDocuments,
        onboardingComplete: onboardingComplete ?? this.onboardingComplete,
        createdAt: createdAt,
        updatedAt: DateTime.now(),
      );

  Map<String, dynamic> toJson() => {
    'id': id,
    'personal': personal.toJson(),
    'contact': contact.toJson(),
    'address': address.toJson(),
    'demographic': demographic.toJson(),
    'status': status.toJson(),
    'school': school.toJson(),
    'nextOfKin': nextOfKin.toJson(),
    'accountContact': accountContact.toJson(),
    'results': results.toJson(),
    'qualification': qualification.toJson(),
    'agreement': agreement.toJson(),
    'uploadedDocuments': uploadedDocuments,
    'grade11Subjects': grade11Subjects.map((s) => s.toJson()).toList(),
    'grade12Subjects': grade12Subjects.map((s) => s.toJson()).toList(),
    'preferredUniversities': preferredUniversities,
    'preferredCourses': preferredCourses,
    'careerInterests': careerInterests,
    'onboardingComplete': onboardingComplete,
    'createdAt': createdAt.toIso8601String(),
    'updatedAt': updatedAt.toIso8601String(),
  };

  factory StudentProfile.fromJson(Map<String, dynamic> json) => StudentProfile(
    id: json['id'] ?? '',
    personal: PersonalDetails.fromJson(json['personal'] ?? {}),
    contact: ContactInfo.fromJson(json['contact'] ?? {}),
    address: AddressInfo.fromJson(json['address'] ?? {}),
    demographic: DemographicInfo.fromJson(json['demographic'] ?? {}),
    status: StatusInfo.fromJson(json['status'] ?? {}),
    school: SchoolInfo.fromJson(json['school'] ?? {}),
    nextOfKin: NextOfKin.fromJson(json['nextOfKin'] ?? {}),
    accountContact: AccountContact.fromJson(json['accountContact'] ?? {}),
    results: ResultsInfo.fromJson(json['results'] ?? {}),
    qualification: QualificationInfo.fromJson(json['qualification'] ?? {}),
    agreement: AgreementInfo.fromJson(json['agreement'] ?? {}),
    uploadedDocuments: (json['uploadedDocuments'] as List?)?.cast<String>() ?? [],
    grade11Subjects: (json['grade11Subjects'] as List?)?.map((s) => SubjectMark.fromJson(s)).toList() ?? [],
    grade12Subjects: (json['grade12Subjects'] as List?)?.map((s) => SubjectMark.fromJson(s)).toList() ?? [],
    preferredUniversities: List<String>.from(json['preferredUniversities'] ?? []),
    preferredCourses: List<String>.from(json['preferredCourses'] ?? []),
    careerInterests: List<String>.from(json['careerInterests'] ?? []),
    onboardingComplete: json['onboardingComplete'] ?? false,
    createdAt: json['createdAt'] != null ? DateTime.parse(json['createdAt']) : DateTime.now(),
    updatedAt: json['updatedAt'] != null ? DateTime.parse(json['updatedAt']) : DateTime.now(),
  );
}

class SubjectMark {
  final String subject;
  final int level;
  final double mark;

  const SubjectMark({required this.subject, this.level = 0, required this.mark});

  Map<String, dynamic> toJson() => {'subject': subject, 'level': level, 'mark': mark};

  factory SubjectMark.fromJson(Map<String, dynamic> json) => SubjectMark(
    subject: json['subject'] ?? '',
    level: json['level'] ?? 0,
    mark: (json['mark'] ?? 0).toDouble(),
  );

  SubjectMark copyWith({String? subject, int? level, double? mark}) => SubjectMark(
    subject: subject ?? this.subject,
    level: level ?? this.level,
    mark: mark ?? this.mark,
  );
}