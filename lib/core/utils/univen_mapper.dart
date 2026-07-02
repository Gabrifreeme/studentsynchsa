import 'package:studentsyncsa/domain/models/student_profile.dart';

class UnivenMapper {
  static Map<String, dynamic> mapProfileToUniven(StudentProfile p) {
    return {
      // --- Personal ---
      'oapTitle': _mapTitle(p.personal.title),
      'oapInitials': p.personal.initials,
      'oapFirstNames': p.personal.firstName,
      'oapSurname': p.personal.lastName,
      'oapMaidenName': p.personal.maidenName,
      'oapID': p.personal.idNumber,
      'oapGender': _mapGender(p.personal.gender),
      'oapDOB': p.personal.dateOfBirth?.toString().substring(0, 10),
      // --- Contact ---
      'oapEmail': p.contact.email,
      'oapCell': p.contact.phone,
      'oapWorkPhone': p.contact.workPhone,
      // --- Demographic ---
      'oapCitizenType': _mapCitizenship(p.demographic.nationality),
      'oapHomeLang': _mapLanguage(p.demographic.homeLanguage),
      'oapEthnic': _mapPopulation(p.demographic.populationGroup),
      'oapMaritalStatus': _mapMarital(p.demographic.maritalStatus),
      // --- Next of Kin ---
      'oapGuardName': p.nextOfKin.name,
      'oapGuardCell': p.nextOfKin.mobilePhone,
      'oapGuardEmail': p.nextOfKin.email,
      'oapGuardAddr1': p.nextOfKin.addressLine1,
      'oapGuardPostalCode': p.nextOfKin.postalCode,
      // --- School & Qualification ---
      'oapSchool': p.school.schoolName,
      'oapGrade': p.school.currentGrade,
      'oapMatricYear': p.results.matricYear.toString(),
      'oapFaculty': p.qualification.choices.isNotEmpty ? p.qualification.choices.first.faculty : '',
      'oapProgramme': p.qualification.choices.isNotEmpty ? p.qualification.choices.first.programme : '',
    };
  }

  // --- HELPERS: You match these numbers to the index of the dropdown item ---
  static int _mapGender(String g) => g == 'Male' ? 2 : 1;
  static int _mapTitle(String t) => ['Mr', 'Ms', 'Mx', 'Dr', 'Prof'].indexOf(t) + 1;
  static int _mapMarital(String m) => ['Single', 'Married', 'Divorced', 'Widowed'].indexOf(m) + 1;
  static int _mapCitizenship(String c) => c == 'SA Citizen' ? 1 : 2;
  static int _mapPopulation(String p) => ['African', 'Black', 'Coloured', 'Indian/Asian', 'White'].indexOf(p) + 1;
  static int _mapLanguage(String l) => ['ENGLISH', 'AFRIKAANS', 'VENDA', 'ZULU', 'XHOSA'].indexOf(l) + 1;
}
