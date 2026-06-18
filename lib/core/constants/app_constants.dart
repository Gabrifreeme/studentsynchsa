class AppConstants {
  AppConstants._();

  static const String appName = 'StudentSynchSA';
  static const String appTagline = 'Your university application companion';

  // AI / Star
  static const String aiName = 'Star';
  static const String aiTagline = 'Your smart university guide';

  // Google Sign-In
  static const String googleClientId =
      '864470911027-46ogt1qabojutsfp698rr5kvs4acudl4.apps.googleusercontent.com';

  // Server
  static const String serverUrl = 'http://127.0.0.1:8773';
  static const int serverPort = 8773;

  // Hive box names
  static const String profileBox = 'student_profile';
  static const String applicationsBox = 'applications';
  static const String universitiesBox = 'universities';
  static const String bursariesBox = 'bursaries';
  static const String notificationsBox = 'notifications';
  static const String settingsBox = 'settings';

  // Sync
  static const Duration syncInterval = Duration(minutes: 5);
  static const Duration requestTimeout = Duration(seconds: 30);

  // Profile
  static const List<String> provinces = [
    'Eastern Cape',
    'Free State',
    'Gauteng',
    'KwaZulu-Natal',
    'Limpopo',
    'Mpumalanga',
    'Northern Cape',
    'North West',
    'Western Cape',
  ];

  static const List<String> grades = [
    'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12',
    'Completed Grade 12',
  ];

  static const List<String> subjects = [
    'English Home Language',
    'English First Additional Language',
    'Afrikaans Home Language',
    'Afrikaans First Additional Language',
    'isiXhosa Home Language',
    'isiXhosa First Additional Language',
    'isiZulu Home Language',
    'isiZulu First Additional Language',
    'Sepedi Home Language',
    'Sepedi First Additional Language',
    'Sesotho Home Language',
    'Sesotho First Additional Language',
    'Setswana Home Language',
    'Setswana First Additional Language',
    'siSwati Home Language',
    'siSwati First Additional Language',
    'Tshivenda Home Language',
    'Tshivenda First Additional Language',
    'Xitsonga Home Language',
    'Xitsonga First Additional Language',
    'Mathematics',
    'Mathematical Literacy',
    'Physical Sciences',
    'Life Sciences',
    'Accounting',
    'Business Studies',
    'Economics',
    'Geography',
    'History',
    'Life Orientation',
    'Information Technology',
    'Computer Applications Technology',
    'Agricultural Sciences',
    'Tourism',
    'Visual Arts',
    'Dramatic Arts',
    'Music',
    'Religion Studies',
    'Engineering Graphics and Design',
  ];

  static const List<String> careerInterests = [
    'Health Sciences',
    'Engineering',
    'Law',
    'Business & Finance',
    'Education',
    'Arts & Humanities',
    'Science & Technology',
    'Social Sciences',
    'Agriculture',
    'Information Technology',
  ];
}
