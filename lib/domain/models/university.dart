import 'package:studentsyncsa/domain/models/offline_resource.dart';

class University {
  final String id;
  final String name;
  final String shortName;
  final String description;
  final String province;
  final String website;
  final String applicationUrl;
  final String logoUrl;
  final DateTime? applicationOpenDate;
  final DateTime? applicationCloseDate;
  final bool hasApplicationFee;
  final double? applicationFee;
  final bool requiresNbt;
  final int? minimumAps;
  final List<String> requirements;
  final List<String> faculties;
  final List<String> courses;
  final bool isPublic;
  final List<OfflineResource> offlineResources;
  final String phone;
  final String email;
  final String address;
  final Map<String, String> socialMedia;

  const University({
    required this.id,
    required this.name,
    required this.shortName,
    this.description = '',
    required this.province,
    this.website = '',
    this.applicationUrl = '',
    this.logoUrl = '',
    this.applicationOpenDate,
    this.applicationCloseDate,
    this.hasApplicationFee = false,
    this.applicationFee,
    this.requiresNbt = false,
    this.minimumAps,
    this.requirements = const [],
    this.faculties = const [],
    this.courses = const [],
    this.isPublic = true,
    this.offlineResources = const [],
    this.phone = '',
    this.email = '',
    this.address = '',
    this.socialMedia = const {},
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'shortName': shortName,
    'description': description,
    'province': province,
    'website': website,
    'applicationUrl': applicationUrl,
    'logoUrl': logoUrl,
    'applicationOpenDate': applicationOpenDate?.toIso8601String(),
    'applicationCloseDate': applicationCloseDate?.toIso8601String(),
    'hasApplicationFee': hasApplicationFee,
    'applicationFee': applicationFee,
    'requiresNbt': requiresNbt,
    'minimumAps': minimumAps,
    'requirements': requirements,
    'faculties': faculties,
    'courses': courses,
    'isPublic': isPublic,
    'offlineResources': offlineResources.map((r) => r.toJson()).toList(),
    'phone': phone,
    'email': email,
    'address': address,
    'socialMedia': socialMedia,
  };

  factory University.fromJson(Map<String, dynamic> json) => University(
    id: json['id'] ?? '',
    name: json['name'] ?? '',
    shortName: json['shortName'] ?? '',
    description: json['description'] ?? '',
    province: json['province'] ?? '',
    website: json['website'] ?? '',
    applicationUrl: json['applicationUrl'] ?? '',
    logoUrl: json['logoUrl'] ?? '',
    applicationOpenDate: json['applicationOpenDate'] != null ? DateTime.tryParse(json['applicationOpenDate']) : null,
    applicationCloseDate: json['applicationCloseDate'] != null ? DateTime.tryParse(json['applicationCloseDate']) : null,
    hasApplicationFee: json['hasApplicationFee'] ?? false,
    applicationFee: (json['applicationFee'] as num?)?.toDouble(),
    requiresNbt: json['requiresNbt'] ?? false,
    minimumAps: json['minimumAps'],
    requirements: List<String>.from(json['requirements'] ?? []),
    faculties: List<String>.from(json['faculties'] ?? []),
    courses: List<String>.from(json['courses'] ?? []),
    isPublic: json['isPublic'] ?? true,
    offlineResources: (json['offlineResources'] as List?)
        ?.map((r) => OfflineResource.fromJson(r))
        .toList() ?? [],
    phone: json['phone'] ?? '',
    email: json['email'] ?? '',
    address: json['address'] ?? '',
    socialMedia: Map<String, String>.from(json['socialMedia'] as Map? ?? {}),
  );
}
