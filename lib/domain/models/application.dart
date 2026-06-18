enum ApplicationStatus {
  notStarted,
  inProgress,
  submitted,
  waitingResponse,
  accepted,
  rejected,
  needMoreDocuments;

  String get label {
    switch (this) {
      case notStarted: return 'Not Started';
      case inProgress: return 'In Progress';
      case submitted: return 'Submitted';
      case waitingResponse: return 'Waiting for Response';
      case accepted: return 'Accepted';
      case rejected: return 'Rejected';
      case needMoreDocuments: return 'Need More Documents';
    }
  }
}

class UniversityApplication {
  final String id;
  final String universityId;
  final String universityName;
  final String course;
  final String faculty;
  final DateTime submissionDate;
  final ApplicationStatus status;
  final bool feePaid;
  final bool nbtCompleted;
  final List<String> documentsSubmitted;
  final String notes;
  final List<DateTime> reminderDates;
  final DateTime createdAt;
  final DateTime updatedAt;

  UniversityApplication({
    required this.id,
    required this.universityId,
    required this.universityName,
    this.course = '',
    this.faculty = '',
    DateTime? submissionDate,
    this.status = ApplicationStatus.notStarted,
    this.feePaid = false,
    this.nbtCompleted = false,
    this.documentsSubmitted = const [],
    this.notes = '',
    this.reminderDates = const [],
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : submissionDate = submissionDate ?? DateTime.now(),
        createdAt = createdAt ?? DateTime.now(),
        updatedAt = updatedAt ?? DateTime.now();

  UniversityApplication copyWith({
    String? universityName,
    String? course,
    String? faculty,
    DateTime? submissionDate,
    ApplicationStatus? status,
    bool? feePaid,
    bool? nbtCompleted,
    List<String>? documentsSubmitted,
    String? notes,
    List<DateTime>? reminderDates,
  }) {
    return UniversityApplication(
      id: id,
      universityId: universityId,
      universityName: universityName ?? this.universityName,
      course: course ?? this.course,
      faculty: faculty ?? this.faculty,
      submissionDate: submissionDate ?? this.submissionDate,
      status: status ?? this.status,
      feePaid: feePaid ?? this.feePaid,
      nbtCompleted: nbtCompleted ?? this.nbtCompleted,
      documentsSubmitted: documentsSubmitted ?? this.documentsSubmitted,
      notes: notes ?? this.notes,
      reminderDates: reminderDates ?? this.reminderDates,
      createdAt: createdAt,
      updatedAt: DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'universityId': universityId,
    'universityName': universityName,
    'course': course,
    'faculty': faculty,
    'submissionDate': submissionDate.toIso8601String(),
    'status': status.name,
    'feePaid': feePaid,
    'nbtCompleted': nbtCompleted,
    'documentsSubmitted': documentsSubmitted,
    'notes': notes,
    'reminderDates': reminderDates.map((d) => d.toIso8601String()).toList(),
    'createdAt': createdAt.toIso8601String(),
    'updatedAt': updatedAt.toIso8601String(),
  };

  factory UniversityApplication.fromJson(Map<String, dynamic> json) => UniversityApplication(
    id: json['id'] ?? '',
    universityId: json['universityId'] ?? '',
    universityName: json['universityName'] ?? '',
    course: json['course'] ?? '',
    faculty: json['faculty'] ?? '',
    submissionDate: DateTime.parse(json['submissionDate']),
    status: ApplicationStatus.values.firstWhere((s) => s.name == json['status'], orElse: () => ApplicationStatus.notStarted),
    feePaid: json['feePaid'] ?? false,
    nbtCompleted: json['nbtCompleted'] ?? false,
    documentsSubmitted: List<String>.from(json['documentsSubmitted'] ?? []),
    notes: json['notes'] ?? '',
    reminderDates: (json['reminderDates'] as List?)?.map((d) => DateTime.parse(d)).toList() ?? [],
    createdAt: DateTime.parse(json['createdAt']),
    updatedAt: DateTime.parse(json['updatedAt']),
  );
}
