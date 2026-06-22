import 'package:studentsyncsa/domain/models/student_profile.dart';

class ProfileValidator {
  static const _required = [
    'personal.firstName',
    'personal.lastName',
    'personal.idNumber',
    'contact.email',
    'contact.phone',
  ];

  static List<String> missingFields(StudentProfile profile) {
    final missing = <String>[];
    final labels = <String, String>{
      'personal.firstName': 'First Name',
      'personal.lastName': 'Last Name',
      'personal.idNumber': 'ID Number',
      'contact.email': 'Email',
      'contact.phone': 'Phone',
    };

    for (final path in _required) {
      final value = _resolve(profile, path);
      if (value == null || value.toString().trim().isEmpty) {
        missing.add(labels[path] ?? path);
      }
    }
    return missing;
  }

  static dynamic _resolve(StudentProfile profile, String path) {
    final parts = path.split('.');
    if (parts.length == 2) {
      switch (parts[0]) {
        case 'personal':
          final m = profile.personal.toJson();
          return m[parts[1]];
        case 'contact':
          final m = profile.contact.toJson();
          return m[parts[1]];
      }
    }
    return null;
  }
}
