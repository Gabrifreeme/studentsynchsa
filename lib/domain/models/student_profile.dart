class StudentProfile {
  final String id;
  final String email;
  final String firstName;
  final String lastName;
  final String idNumber;
  final DateTime? dateOfBirth;
  final String gender;
  final String nationality;
  final String phone;
  final String address;
  final String province;
  final String schoolName;
  final String currentGrade;
  final String yearOfMatric;
  final List<SubjectMark> grade11Subjects;
  final List<SubjectMark> grade12Subjects;
  final List<String> preferredUniversities;
  final List<String> preferredCourses;
  final List<String> careerInterests;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool onboardingComplete;

  StudentProfile({
    required this.id,
    this.email = '',
    this.firstName = '',
    this.lastName = '',
    this.idNumber = '',
    this.dateOfBirth,
    this.gender = '',
    this.nationality = 'South African',
    this.phone = '',
    this.address = '',
    this.province = '',
    this.schoolName = '',
    this.currentGrade = '',
    this.yearOfMatric = '',
    this.grade11Subjects = const [],
    this.grade12Subjects = const [],
    this.preferredUniversities = const [],
    this.preferredCourses = const [],
    this.careerInterests = const [],
    this.onboardingComplete = false,
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : createdAt = createdAt ?? DateTime.now(),
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
    String? email,
    String? firstName,
    String? lastName,
    String? idNumber,
    DateTime? dateOfBirth,
    String? gender,
    String? nationality,
    String? phone,
    String? address,
    String? province,
    String? schoolName,
    String? currentGrade,
    String? yearOfMatric,
    List<SubjectMark>? grade11Subjects,
    List<SubjectMark>? grade12Subjects,
    List<String>? preferredUniversities,
    List<String>? preferredCourses,
    List<String>? careerInterests,
    bool? onboardingComplete,
  }) {
    return StudentProfile(
      id: id,
      email: email ?? this.email,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      idNumber: idNumber ?? this.idNumber,
      dateOfBirth: dateOfBirth ?? this.dateOfBirth,
      gender: gender ?? this.gender,
      nationality: nationality ?? this.nationality,
      phone: phone ?? this.phone,
      address: address ?? this.address,
      province: province ?? this.province,
      schoolName: schoolName ?? this.schoolName,
      currentGrade: currentGrade ?? this.currentGrade,
      yearOfMatric: yearOfMatric ?? this.yearOfMatric,
      grade11Subjects: grade11Subjects ?? this.grade11Subjects,
      grade12Subjects: grade12Subjects ?? this.grade12Subjects,
      preferredUniversities: preferredUniversities ?? this.preferredUniversities,
      preferredCourses: preferredCourses ?? this.preferredCourses,
      careerInterests: careerInterests ?? this.careerInterests,
      onboardingComplete: onboardingComplete ?? this.onboardingComplete,
      createdAt: createdAt,
      updatedAt: DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'firstName': firstName,
    'lastName': lastName,
    'idNumber': idNumber,
    'dateOfBirth': dateOfBirth?.toIso8601String(),
    'gender': gender,
    'nationality': nationality,
    'phone': phone,
    'address': address,
    'province': province,
    'schoolName': schoolName,
    'currentGrade': currentGrade,
    'yearOfMatric': yearOfMatric,
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
    email: json['email'] ?? '',
    firstName: json['firstName'] ?? '',
    lastName: json['lastName'] ?? '',
    idNumber: json['idNumber'] ?? '',
    dateOfBirth: json['dateOfBirth'] != null ? DateTime.tryParse(json['dateOfBirth']) : null,
    gender: json['gender'] ?? '',
    nationality: json['nationality'] ?? 'South African',
    phone: json['phone'] ?? '',
    address: json['address'] ?? '',
    province: json['province'] ?? '',
    schoolName: json['schoolName'] ?? '',
    currentGrade: json['currentGrade'] ?? '',
    yearOfMatric: json['yearOfMatric'] ?? '',
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
  final double mark;

  const SubjectMark({required this.subject, required this.mark});

  Map<String, dynamic> toJson() => {'subject': subject, 'mark': mark};

  factory SubjectMark.fromJson(Map<String, dynamic> json) => SubjectMark(
    subject: json['subject'] ?? '',
    mark: (json['mark'] ?? 0).toDouble(),
  );

  SubjectMark copyWith({String? subject, double? mark}) => SubjectMark(
    subject: subject ?? this.subject,
    mark: mark ?? this.mark,
  );
}
