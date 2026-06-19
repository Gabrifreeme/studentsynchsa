class OfflineResource {
  final String title;
  final String type; // 'pdf' | 'image' | 'doc' | 'map' | 'page'
  final String assetPath; // local asset or bundled URL
  final String? description;
  final String universityId;

  const OfflineResource({
    required this.title,
    required this.type,
    required this.assetPath,
    this.description,
    required this.universityId,
  });

  Map<String, dynamic> toJson() => {
    'title': title,
    'type': type,
    'assetPath': assetPath,
    'description': description,
    'universityId': universityId,
  };

  factory OfflineResource.fromJson(Map<String, dynamic> json) => OfflineResource(
    title: json['title'] ?? '',
    type: json['type'] ?? '',
    assetPath: json['assetPath'] ?? '',
    description: json['description'],
    universityId: json['universityId'] ?? '',
  );
}
