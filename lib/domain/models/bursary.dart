class Bursary {
  final String id;
  final String name;
  final String provider;
  final String description;
  final String eligibility;
  final String website;
  final String applicationUrl;
  final String logoUrl;
  final DateTime? deadline;
  final List<String> fieldsOfStudy;
  final bool requiresUniversityAdmission;
  final double? amount;
  final String coverage;

  const Bursary({
    required this.id,
    required this.name,
    required this.provider,
    this.description = '',
    this.eligibility = '',
    this.website = '',
    this.applicationUrl = '',
    this.logoUrl = '',
    this.deadline,
    this.fieldsOfStudy = const [],
    this.requiresUniversityAdmission = false,
    this.amount,
    this.coverage = '',
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'provider': provider,
    'description': description,
    'eligibility': eligibility,
    'website': website,
    'applicationUrl': applicationUrl,
    'logoUrl': logoUrl,
    'deadline': deadline?.toIso8601String(),
    'fieldsOfStudy': fieldsOfStudy,
    'requiresUniversityAdmission': requiresUniversityAdmission,
    'amount': amount,
    'coverage': coverage,
  };

  factory Bursary.fromJson(Map<String, dynamic> json) => Bursary(
    id: json['id'] ?? '',
    name: json['name'] ?? '',
    provider: json['provider'] ?? '',
    description: json['description'] ?? '',
    eligibility: json['eligibility'] ?? '',
    website: json['website'] ?? '',
    applicationUrl: json['applicationUrl'] ?? '',
    logoUrl: json['logoUrl'] ?? '',
    deadline: json['deadline'] != null ? DateTime.tryParse(json['deadline']) : null,
    fieldsOfStudy: List<String>.from(json['fieldsOfStudy'] ?? []),
    requiresUniversityAdmission: json['requiresUniversityAdmission'] ?? false,
    amount: (json['amount'] as num?)?.toDouble(),
    coverage: json['coverage'] ?? '',
  );
}

enum BursaryApplicationStatus {
  notApplied,
  inProgress,
  submitted,
  waitingResponse,
  awarded,
  rejected;

  String get label {
    switch (this) {
      case notApplied: return 'Not Applied';
      case inProgress: return 'In Progress';
      case submitted: return 'Submitted';
      case waitingResponse: return 'Waiting for Response';
      case awarded: return 'Awarded';
      case rejected: return 'Rejected';
    }
  }
}

class BursaryApplication {
  final String id;
  final String bursaryId;
  final String bursaryName;
  final BursaryApplicationStatus status;
  final DateTime applicationDate;
  final List<String> documentsSubmitted;
  final String notes;
  final DateTime createdAt;
  final DateTime updatedAt;

  BursaryApplication({
    required this.id,
    required this.bursaryId,
    required this.bursaryName,
    this.status = BursaryApplicationStatus.notApplied,
    DateTime? applicationDate,
    this.documentsSubmitted = const [],
    this.notes = '',
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : applicationDate = applicationDate ?? DateTime.now(),
        createdAt = createdAt ?? DateTime.now(),
        updatedAt = updatedAt ?? DateTime.now();

  Map<String, dynamic> toJson() => {
    'id': id,
    'bursaryId': bursaryId,
    'bursaryName': bursaryName,
    'status': status.name,
    'applicationDate': applicationDate.toIso8601String(),
    'documentsSubmitted': documentsSubmitted,
    'notes': notes,
    'createdAt': createdAt.toIso8601String(),
    'updatedAt': updatedAt.toIso8601String(),
  };

  factory BursaryApplication.fromJson(Map<String, dynamic> json) => BursaryApplication(
    id: json['id'] ?? '',
    bursaryId: json['bursaryId'] ?? '',
    bursaryName: json['bursaryName'] ?? '',
    status: BursaryApplicationStatus.values.firstWhere((s) => s.name == json['status'], orElse: () => BursaryApplicationStatus.notApplied),
    applicationDate: DateTime.parse(json['applicationDate']),
    documentsSubmitted: List<String>.from(json['documentsSubmitted'] ?? []),
    notes: json['notes'] ?? '',
    createdAt: DateTime.parse(json['createdAt']),
    updatedAt: DateTime.parse(json['updatedAt']),
  );
}
