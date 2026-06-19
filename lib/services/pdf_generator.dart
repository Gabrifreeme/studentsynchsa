import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:studentsyncsa/domain/models/student_profile.dart';

class PdfGenerator {
  Future<List<int>> generateApplicationPdf(StudentProfile profile, {String universityName = ''}) async {
    final pdf = pw.Document();
    final dateFormat = DateFormat('dd MMMM yyyy');
    final theme = _PdfTheme();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(40),
        build: (ctx) => [
          _buildHeader(profile, universityName, theme),
          _buildSection('Personal Information', [
            _field('Title', profile.personal.title),
            _field('Initials', profile.personal.initials),
            _field('First Name', profile.personal.firstName),
            _field('Last Name', profile.personal.lastName),
            _field('Maiden Name', profile.personal.maidenName),
            _field('Gender', profile.personal.gender),
            _field('Date of Birth', profile.personal.dateOfBirth != null ? dateFormat.format(profile.personal.dateOfBirth!) : ''),
            _field('ID Number', profile.personal.idNumber),
          ], theme),
          _buildSection('Contact Information', [
            _field('Email', profile.contact.email),
            _field('Phone', profile.contact.phone),
            _field('Work Phone', profile.contact.workPhone),
          ], theme),
          _buildSection('Address', [
            _field('Address Line 1', profile.address.address),
            _field('Address Line 2', profile.address.addressLine2),
            _field('Address Line 3', profile.address.addressLine3),
            _field('Province', profile.address.province),
            _field('Postal Code', profile.address.postalCode),
          ], theme),
          _buildSection('Demographic Information', [
            _field('Nationality', profile.demographic.nationality),
            _field('Country of Birth', profile.demographic.countryOfBirth),
            _field('Home Language', profile.demographic.homeLanguage),
            _field('Population Group', profile.demographic.populationGroup),
            _field('Marital Status', profile.demographic.maritalStatus),
          ], theme),
          _buildSection('Status', [
            _field('Disability Status', profile.status.disabilityStatus),
            _field('Bursary Required', profile.status.bursaryRequired),
            _field('Employment Status', profile.status.employmentStatus),
          ], theme),
          _buildSection('School Information', [
            _field('School Name', profile.school.schoolName),
            _field('Current Grade', profile.school.currentGrade),
            _field('Year of Matric', profile.school.yearOfMatric),
            _field('Currently Doing', profile.school.currentlyDoing),
            _field('Studied Previously', profile.school.studiedPreviously),
          ], theme),
          _buildSubjects(profile, theme),
          _buildSection('Results', [
            _field('Matric Year', profile.results.matricYear > 0 ? profile.results.matricYear.toString() : ''),
            _field('Application Level', profile.results.applicationLevel),
            _field('Upgrading', profile.results.upgrading),
            _field('Matric Type', profile.results.matricType),
            _field('Examination Number', profile.results.examinationNumber),
            _field('School Leaving Certificate', profile.results.schoolLeavingCertificate),
          ], theme),
          _buildSection('Qualification', [
            _field('Academic Year', profile.qualification.academicYear > 0 ? profile.qualification.academicYear.toString() : ''),
            _field('Faculty', profile.qualification.choices.isNotEmpty ? profile.qualification.choices.first.faculty : ''),
            _field('Programme', profile.qualification.choices.isNotEmpty ? profile.qualification.choices.first.programme : ''),
            _field('Application Period', profile.qualification.applicationPeriod),
            _field('Study Mode', profile.qualification.studyMode),
            _field('Study Timing', profile.qualification.studyTiming),
          ], theme),
          _buildSection('Next of Kin', [
            _field('Name', profile.nextOfKin.name),
            _field('Mobile Phone', profile.nextOfKin.mobilePhone),
            _field('Home Phone', profile.nextOfKin.homePhone),
            _field('Work Phone', profile.nextOfKin.workPhone),
            _field('Email', profile.nextOfKin.email),
            _field('Address', [
              profile.nextOfKin.addressLine1,
              profile.nextOfKin.addressLine2,
              profile.nextOfKin.addressLine3,
              profile.nextOfKin.addressLine4,
              profile.nextOfKin.postalCode,
            ].where((l) => l.isNotEmpty).join(', ')),
          ], theme),
          _buildSection('Account Contact', [
            _field('Name', profile.accountContact.name),
            _field('Mobile Phone', profile.accountContact.mobilePhone),
            _field('Home Phone', profile.accountContact.homePhone),
            _field('Email', profile.accountContact.email),
            _field('Address', [
              profile.accountContact.addressLine1,
              profile.accountContact.addressLine2,
              profile.accountContact.addressLine3,
              profile.accountContact.addressLine4,
              profile.accountContact.postalCode,
            ].where((l) => l.isNotEmpty).join(', ')),
          ], theme),
          _buildSection('Agreement', [
            _field('Login Pin', profile.agreement.loginPin),
            _field('Acceptance Status', profile.agreement.acceptanceStatus),
          ], theme),
          if (profile.careerInterests.isNotEmpty)
            _buildSection('Career Interests', [
              _field('', profile.careerInterests.join(', ')),
            ], theme),
          if (profile.preferredUniversities.isNotEmpty)
            _buildSection('Preferred Universities', [
              _field('', profile.preferredUniversities.join(', ')),
            ], theme),
          if (profile.preferredCourses.isNotEmpty)
            _buildSection('Preferred Courses', [
              _field('', profile.preferredCourses.join(', ')),
            ], theme),
        ],
      ),
    );

    return await pdf.save();
  }

  pw.Widget _buildHeader(StudentProfile profile, String universityName, _PdfTheme theme) {
    return pw.Column(
      children: [
        pw.Center(
          child: pw.Text(
            universityName.isNotEmpty ? universityName : 'University Application',
            style: pw.TextStyle(fontSize: 20, fontWeight: pw.FontWeight.bold, color: theme.primaryColor),
          ),
        ),
        pw.SizedBox(height: 4),
        pw.Center(
          child: pw.Text(
            'Pre-filled Application Form',
            style: pw.TextStyle(fontSize: 12, color: PdfColors.grey600),
          ),
        ),
        pw.SizedBox(height: 4),
        pw.Center(
          child: pw.Text(
            'Generated on ${DateFormat('dd MMMM yyyy').format(DateTime.now())}',
            style: pw.TextStyle(fontSize: 9, color: PdfColors.grey400),
          ),
        ),
        pw.Divider(color: theme.primaryColor, thickness: 1.5),
        pw.SizedBox(height: 12),
      ],
    );
  }

  pw.Widget _buildSection(String title, List<pw.Widget> fields, _PdfTheme theme) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Container(
          color: theme.sectionBg,
          padding: const pw.EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: pw.Text(title,
            style: pw.TextStyle(
              fontSize: 13,
              fontWeight: pw.FontWeight.bold,
              color: theme.primaryColor,
            ),
          ),
        ),
        pw.SizedBox(height: 6),
        ...fields,
        pw.SizedBox(height: 12),
      ],
    );
  }

  pw.Widget _field(String label, String value) {
    if (value.isEmpty) return pw.SizedBox();
    return pw.Padding(
      padding: const pw.EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          if (label.isNotEmpty)
            pw.SizedBox(
              width: 140,
              child: pw.Text(label + ':',
                style: pw.TextStyle(
                  fontSize: 10,
                  fontWeight: pw.FontWeight.bold,
                  color: PdfColors.grey700,
                ),
              ),
            ),
          pw.Expanded(
            child: pw.Text(value,
              style: const pw.TextStyle(fontSize: 10, color: PdfColors.black),
            ),
          ),
        ],
      ),
    );
  }

  pw.Widget _buildSubjects(StudentProfile profile, _PdfTheme theme) {
    final subjects = profile.results.subjects;
    if (subjects.isEmpty) return pw.SizedBox();
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        pw.Container(
          color: theme.sectionBg,
          padding: const pw.EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          child: pw.Text('Subjects',
            style: pw.TextStyle(
              fontSize: 13,
              fontWeight: pw.FontWeight.bold,
              color: theme.primaryColor,
            ),
          ),
        ),
        pw.SizedBox(height: 6),
        pw.Table(
          border: pw.TableBorder.all(color: PdfColors.grey300, width: 0.5),
          children: [
            pw.TableRow(
              decoration: pw.BoxDecoration(color: PdfColors.grey100),
              children: ['Subject', 'Grade', 'Result', 'Symbol']
                  .map((h) => pw.Padding(
                        padding: const pw.EdgeInsets.all(6),
                        child: pw.Text(h, style: pw.TextStyle(fontSize: 10, fontWeight: pw.FontWeight.bold)),
                      ))
                  .toList(),
            ),
            ...subjects.map((s) => pw.TableRow(
                  children: [s.subject, s.grade, s.result, s.symbol]
                      .map((c) => pw.Padding(
                            padding: const pw.EdgeInsets.all(6),
                            child: pw.Text(c, style: const pw.TextStyle(fontSize: 9)),
                          ))
                      .toList(),
                )),
          ],
        ),
        pw.SizedBox(height: 12),
      ],
    );
  }

  List<int> _grade12Subjects() => [];
}

class _PdfTheme {
  final PdfColor primaryColor = PdfColors.blue800;
  final PdfColor sectionBg = PdfColors.blue50;
}
