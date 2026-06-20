import 'dart:async';
import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/utils/file_upload.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';
import 'package:studentsyncsa/core/constants/app_constants.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/datasources/local/hive_database.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/presentation/providers/auth_provider.dart';
import 'package:studentsyncsa/presentation/providers/profile_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class ProfileOnboardingScreen extends ConsumerStatefulWidget {
  const ProfileOnboardingScreen({super.key});

  @override
  ConsumerState<ProfileOnboardingScreen> createState() =>
      _ProfileOnboardingScreenState();
}

class _ProfileOnboardingScreenState
    extends ConsumerState<ProfileOnboardingScreen>
    with SingleTickerProviderStateMixin {
  final _pageController = PageController();
  int _currentPage = 0;
  bool _showGreeting = true;
  int _visibleChars = 0;
  late AnimationController _floatCtrl;
  late Animation<double> _floatAnim;

  // Personal Details
  final _titleCtrl = TextEditingController();
  final _initialsCtrl = TextEditingController();
  final _firstNameCtrl = TextEditingController();
  final _lastNameCtrl = TextEditingController();
  final _maidenNameCtrl = TextEditingController();
  final _idCtrl = TextEditingController();
  String _gender = '';
  DateTime? _selectedDob;

  // Demographic
  String _citizenship = 'RSA';
  final _countryOfBirthCtrl = TextEditingController();
  final _homeLanguageCtrl = TextEditingController();
  String _populationGroup = '';
  String _maritalStatus = '';

  // Contact
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _workPhoneCtrl = TextEditingController();

  // Address
  final _addressCtrl = TextEditingController();
  final _addressLine2Ctrl = TextEditingController();
  final _addressLine3Ctrl = TextEditingController();
  String _province = '';
  final _postalCodeCtrl = TextEditingController();
  final _postalAddressCtrl = TextEditingController();
  bool _postalSameAsResidential = false;

  // Status
  String _disabilityStatus = '';
  String _bursaryRequired = '';
  String _employmentStatus = '';

  // School & Subjects
  final _schoolCtrl = TextEditingController();
  String _grade = '';
  List<SubjectMark> _subjects = [];
  List<String> _careerInterests = [];

  // Next of Kin
  final _nextOfKinNameCtrl = TextEditingController();
  final _nextOfKinMobileCtrl = TextEditingController();
  final _nextOfKinHomePhoneCtrl = TextEditingController();
  final _nextOfKinWorkPhoneCtrl = TextEditingController();
  final _nextOfKinAddr1Ctrl = TextEditingController();
  final _nextOfKinAddr2Ctrl = TextEditingController();
  final _nextOfKinAddr3Ctrl = TextEditingController();
  final _nextOfKinAddr4Ctrl = TextEditingController();
  final _nextOfKinPostalCodeCtrl = TextEditingController();
  final _nextOfKinEmailCtrl = TextEditingController();

  // Account Contact
  final _accountContactNameCtrl = TextEditingController();
  final _accountContactMobileCtrl = TextEditingController();
  final _accountContactHomePhoneCtrl = TextEditingController();
  final _accountContactAddr1Ctrl = TextEditingController();
  final _accountContactAddr2Ctrl = TextEditingController();
  final _accountContactAddr3Ctrl = TextEditingController();
  final _accountContactAddr4Ctrl = TextEditingController();
  final _accountContactPostalCodeCtrl = TextEditingController();
  final _accountContactEmailCtrl = TextEditingController();

  // Results
  int _matricYear = 0;
  String _applicationLevel = '';
  String _upgrading = '';
  String _matricType = '';
  final _examinationNumberCtrl = TextEditingController();
  final _schoolLeavingCertCtrl = TextEditingController();
  String get _schoolLeavingCertificate => _schoolLeavingCertCtrl.text;
  set _schoolLeavingCertificate(String v) => _schoolLeavingCertCtrl.text = v;
  List<SubjectDetail> _resultsSubjects = [];

  // Educational Institution
  String _currentlyDoing = '';
  String _studiedPreviously = '';

  // Qualification
  int _academicYear = 0;
  final _facultyCtrl = TextEditingController();
  final _programmeCtrl = TextEditingController();
  String _applicationPeriod = '';
  String _studyMode = '';
  String _studyTiming = '';

  // Agreement
  final _loginPinCtrl = TextEditingController();
  String _acceptanceStatus = '';

  // Upload Documents
  final List<String> _uploadedFiles = ['', '', ''];

  bool _saving = false;

  final _formKeys = List.generate(7, (_) => GlobalKey<FormState>());
  static const _greetingText = "Hi there! I'm Star ⭐\n\nLet's get to know you so I can help find the perfect universities and bursaries for your future!";

  static const _countryList = [
    'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda',
    'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan',
    'Bahamas', 'Bahrain', 'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize',
    'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil',
    'Brunei', 'Bulgaria', 'Burkina Faso', 'Burundi',
    'Cambodia', 'Cameroon', 'Canada', 'Cape Verde', 'Central African Republic',
    'Chad', 'Chile', 'China', 'Colombia', 'Comoros', 'Congo', 'Costa Rica',
    "Côte d'Ivoire", 'Croatia', 'Cuba', 'Cyprus', 'Czech Republic',
    'Democratic Republic of the Congo', 'Denmark', 'Djibouti', 'Dominica',
    'Dominican Republic',
    'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Estonia',
    'Eswatini', 'Ethiopia',
    'Fiji', 'Finland', 'France',
    'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece', 'Grenada',
    'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana',
    'Haiti', 'Honduras', 'Hungary',
    'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy',
    'Jamaica', 'Japan', 'Jordan',
    'Kazakhstan', 'Kenya', 'Kiribati', 'Kuwait', 'Kyrgyzstan',
    'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya', 'Liechtenstein',
    'Lithuania', 'Luxembourg',
    'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta',
    'Marshall Islands', 'Mauritania', 'Mauritius', 'Mexico', 'Micronesia',
    'Moldova', 'Monaco', 'Mongolia', 'Montenegro', 'Morocco', 'Mozambique',
    'Myanmar',
    'Namibia', 'Nauru', 'Nepal', 'Netherlands', 'New Zealand', 'Nicaragua',
    'Niger', 'Nigeria', 'North Korea', 'North Macedonia', 'Norway',
    'Oman',
    'Pakistan', 'Palau', 'Palestine', 'Panama', 'Papua New Guinea', 'Paraguay',
    'Peru', 'Philippines', 'Poland', 'Portugal',
    'Qatar',
    'Romania', 'Russia', 'Rwanda',
    'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines',
    'Samoa', 'San Marino', 'Sao Tome and Principe', 'Saudi Arabia', 'Senegal',
    'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore', 'Slovakia', 'Slovenia',
    'Solomon Islands', 'Somalia', 'South Africa', 'South Korea', 'South Sudan',
    'Spain', 'Sri Lanka', 'Sudan', 'Suriname', 'Sweden', 'Switzerland', 'Syria',
    'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand', 'Timor-Leste', 'Togo',
    'Tonga', 'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu',
    'Uganda', 'Ukraine', 'United Arab Emirates', 'United Kingdom',
    'United States of America', 'Uruguay', 'Uzbekistan',
    'Vanuatu', 'Vatican City', 'Venezuela', 'Vietnam',
    'Yemen',
    'Zambia', 'Zimbabwe',
  ];

  static const _languages = [
    'AFRIKAANS',
    'AFRIKAANS/ENGLISH',
    'ENGLISH',
    'HINDU',
    'OTHER BLACK LANG',
    'OTHER EUROPEAN LANG',
    'SOTHO(NORTH)',
    'SOTHO(SOUTH)',
    'SWATI',
    'TSONGA',
    'TSWANA',
    'UNKNOWN',
    'VENDA',
    'XHOSA',
    'ZULU',
  ];

  static const _schoolList = [
    'A. MUGAGULI SECONDARY SCHOOL',
    'A.B MAKAPAN SECONDARY SCHOOL',
    'ADOLF MHINGA HIGH SCHOOL',
    'AKANI SECONDARY SCHOOL',
    'ALEXANDRA SECONDARY SCHOOL',
    'AMABHELE SECONDARY SCHOOL',
    'ANCHOR SENIOR SECONDARY SCHOOL',
    'AZWIFARWI SECONDARY SCHOOL',
    "B.K.MATLALA COM. HIGH SCHOOL",
    'B.MATLOSHE SEC. SCHOOL',
    'BAKENBERG SEN. SEC. SCHOOL',
    'BAMBANANI HIGH SCHOOL',
    'BANKUNA SECONDARY SCHOOL',
    'BATLHAPING SECONDARY SCHOOL',
    'BELA-BELA SEN. SEC. SCHOOL',
    'BHUKULANI SENIOR SEC SCHOOL',
    'BJATLADI SEN. SEC. SCHOOL',
    'BLINKKLIP SEN.SEC. SCHOOL',
    'BOITUMELONG SEN SECONDARY',
    'BOKGAGA SECONDARY SCHOOL',
    'BOLEU SEN.SECONDARY SCHOOL',
    'BONDZENI SECONDARY SCHOOL',
    'BONGUMUSA SEN.SEC. SCHOOL',
    'BOPEDI BAPEDI SEC. SCHOOL',
    'BOSAKGO SECONDARY SCHOOL',
    'BOTLHABELO SECONDARY SCHOOL',
    'BOTSIKANA SECONDARY SCHOOL',
    'BP/SOWETAN REWRITE MAT. SCHOOL',
    'C.KEKANA SEN.SEC. SCHOOL',
    'C.MANTHONSI SECONDARY SCHOOL',
    'CAPRICON SECONDARY SCHOOL',
    'CENTRAL SEC. STATE SCHOOL',
    'CHAYAZA SECONDARY SCHOOL',
    'CHIKA SECONDARY SCHOOL',
    'CHUEUEKGOLO SECONDARY SCHOOL',
    'CORRESPONDENCE',
    'D.MATLHABA II SEN.SEC. SCHOOL',
    'D.TSHIVHASE SECONDARY SCHOOL',
    'DAVHANA SECONDARY SCHOOL',
    'DAVID LUVHIMBA SEC.SCHOOL',
    'DAWANA COM. HIGH SCHOOL',
    'DENGA SECONDARY SCHOOL',
    'DENGENYA SEN. SEC. SCHOOL',
    'DIMANI SECONDERY SCHOOL',
    'DIMBANYIKA SECONDARY SCHOOL',
    'DINKWANYANE SECONDARY SCHOOL',
    'DITSEPU SECONDARY SCHOOL',
    'DLANGEZWA HIGH SCHOOL',
    'DOASHO SECONDARY SCHOOL',
    'DR A.T. MOREOSELE HIGH SCHOOL',
    'DR. M.J. MADIBA SEN. SECONDARY',
    'DUVULA MAHUNTSI',
    'DZATA SECONDARY SCHOOL',
    'DZWABONI SECONDARY SCHOOL',
    'E.NXUMALO SEN.SEC. SCHOOL',
    'E.P.P. MHINGA HIGH SCHOOL',
    'EBENEZER SECONDARY SCHOOL',
    'EKANGALA SECONDARY SCHOOL',
    'EKULINDENI SEN. SEC. SCHOOL',
    'EMADWALENI HIGH SCHOOL',
    'EMJINDINI HIGH SCHOOL',
    'F.RASIMPHI SECONDARY SCHOOL',
    'FETAKGOMO SEN.SEC. SCHOOL',
    'FHATUWANI SECONDARY SCHOOL',
    'FHETANI SECONDARY SCHOOL',
    'FRANCISCAN MATRIC PROJECT',
    'FRANK RAVELE SENIOR SEC SCHOOL',
    'FUNZWANI SECONDARY SCHOOL',
    'G.H.FRANZ SECONDARY SCHOOL',
    'G.MASIBE SECONDARY SCHOOL',
    'G.MBULAHENI SECONDARY SCHOOL',
    'GIDJANA SECONDARY SCHOOL',
    'GIYANI SECONDARY SCHOOL',
    'GLEN-COWIE SECONDARY SCHOOL',
    'GOBOLIBI SEN. SEC. SCHOOL',
    'GODIDE SECONDARY SCHOOL',
    'GOJELA SECONDARY SCHOOL',
    'GUVHUKUVHU SECONDARY SCHOOL',
    'GWAMASENGA SECONDARY SCHOOL',
    'GWAMBENI SECONDARY SCHOOL',
    'H.F.TLOU HIGH SCHOOL',
    'H.NTSANWISI SEN.SEC.SCHOOL',
    'H.OPPENHEIMER AGRIC. SCHOOL',
    'HANYANI SENIOR SEC SCHOOL',
    'HERMAN THEBE HIGH SCHOOL',
    'HIPPO VALLEY SEC. SCHOOL',
    'HLABIRWA SCHOOL OF COMMERCE',
    'HLALALAHLE SECONDARY SCHOOL',
    'HLALUKWENI SECONDARY SCHOOL',
    'HLUVUKA SECONDARY SCHOOL',
    'HOFMEYR HIGH SCHOOL',
    'HOLAPONDO HIGH SCHOOL',
    'HOYOHOYO SECONDARY SCHOOL',
    'HUMBELANI SECONDARY SCHOOL',
    'HUMULA SECONDARY SCHOOL',
    'HWITI TERRITORIAL SCHOOL',
    'I.K.NXUMAYO AGRIC.HIGH SCHOOL',
    'I.R.LESOLANG SECONDARY SCHOOL',
    'INHLAKANIPHO SECONDARY SCHOOL',
    'INKOMASI HIGH SCHOOL',
    'IPOPENG SECONDARY SCHOOL',
    'J. MUSHAATHAMA SEC. SCHOOL',
    'J.LAVHENGWA SECONDARY SCHOOL',
    'J.LEDWABA SECONDARY SCHOOL',
    'J.MULAMBILU SECONDARY SCHOOL',
    'J.SIBASA SEN. SECONDARY SCHOOL',
    'J.THIFULUFHELWI SENIOR SEC.',
    'JAMES KHOSA SECONDARY SCHOOL',
    'K.NGIGIDENI SECONDARY SCHOOL',
    'KABELA SECONDARY SCHOOL',
    'KARABI SEN.SECONDARY SCHOOL',
    'KGAHLANAMORULANA HIGH SCHOOL',
    'KGAHLANONG SEN SECONDARY',
    'KGAKANA SEN.SEC. SCHOOL',
    'KGAKGATHU SEN.SEC. SCHOOL',
    'KGALATLOU SECONDARY SCHOOL',
    'KGALEMA SECONDARY SCHOOL',
    'KGAMANYANE HIGH SCHOOL',
    'KGAOLA SECONDARY SCHOOL',
    'KGAPYANE SEN. SEC. SCHOOL',
    'KGARAHARA SECONDARY SCHOOL',
    'KGEALE SEN SEC SCHOOL',
    'KGOKARI SEN.SEC. SCHOOL',
    'KGOKE SECONDARY SCHOOL',
    'KGOLOKO SECONDARY SCHOOL',
    'KGOTHALA SENIOR SEC SCHOOL',
    'KGWADIAMOLEKE SEN.SEC.SCHOOL',
    'KGWANA SEN. SEC. SCHOOL',
    'KGWARATLOU SECONDARY SCHOOL',
    'KGWEKGWE SECONDARY SCHOOL',
    'KHAISO SECONDARY SCHOOL',
    'KHAKHU SECONDARY SCHOOL',
    'KHAMANE SECONDARY SCHOOL',
    'KHAYALAMI SECONDARY SCHOOL',
    'KHESETHWANE HIGH SCHOOL',
    'KHOMANANI SECONDARY SCHOOL',
    'KHUDU SEN. SECONDARY SCHOOL',
    'KHUMBULA SECONDARY SCHOOL',
    'KHWARA SECONDARY SCHOOL',
    'KHWEVHA SECONDARY SCHOOL',
    'KHWINANA SECONDARY SCHOOL',
    'KILNERTON HIGH SCHOOL',
    'KOLOKOSHANI SECONDARY SCHOOL',
    'KOPA SECONDARY SCHOOL',
    'KUTAMA SECONDARY SCHOOL',
    'KWAMHLANGA SECONDARY SCHOOL',
    'L.RATSHALINGWA SEC. SCHOOL',
    'LAMPLOUGH SEN.SEC. SCHOOL',
    'LAMULA JUBILEE HIGH SCHOOL',
    'LAMULELANI SEN. SEC. SCHOOL',
    'LANGA HIGH SCHOOL',
    'LAVELA SENIOR SEC. SCHOOL',
    'LEBOWAKGOMO SEN. SEC. SCHOOL',
    'LEHLABA SEN. SEC. SCHOOL',
    'LEHLABILE SEN.SEC. SCHOOL',
    'LEHLASEDI SECONDARY SCHOOL',
    'LEKETE SECONDARY SCHOOL',
    'LEKHINE SEN.SEC. SCHOOL',
    'LEKOKO SEN. SEC. SCHOOL',
    'LEKOTA SECONDARY SCHOOL',
    'LEMANA SECONDARY SCHOOL',
    'LENEHA TUMISI SECONDARY',
    'LENGAMA SECONDARY SCHOOL',
    'LEOKENG SEN.SEC. SCHOOL',
    'LEOLO SECONDARY SCHOOL',
    'LEPATO M. SECONDARY SCHOOL',
    'LEPELLE SECONDARY SCHOOL',
    'LEPHADIMISHA SEC.SCHOOL',
    'LEREKO SEN.SEC. SCHOOL',
    'LEROTHODI HIGH SCHOOL',
    'LESAILANE SECONDARY SCHOOL',
    'LETAU SEC SCHOOL',
    'LETHEBA SECONDARY SCHOOL',
    'LETSHEGA MALOKWANE HIGH SCHOOL',
    'LETSHELE SEN. SEC. SCHOOL',
    'LIGEGE SECONDARY SCHOOL',
    'LIHAWU SEN. SECONDARY SCHOOL',
    'LIMBEDZI SECONDARY SCHOOL',
    'LIMEHILL SECONDARY SCHOOL',
    'LISHAVHANA SECONDARY SCHOOL',
    'LITSHOVHU SECONDARY SCHOOL',
    'LOALANE SECONDARY SCHOOL',
    'LUATAME SEN. SEC SCHOOL',
    'LUGEBHUTU SECONDARY SCHOOL',
    'LUNANGWE SECONDARY SCHOOL',
    'LUPHAI SECONDARY SCHOOL',
    'LUVHAIVHAI SECONDARY SCHOOL',
    'LUVHIVHINI SECONDARY SCHOOL',
    'LWAMONDO SECONDARY SCHOOL',
    'LWANDANI SECONDARY SCHOOL',
    'LWENZHE SECONDARY SCHOOL',
    'M.G.D. SECONDARY SCHOOL',
    'M.ISAACSON SEC. SCHOOL',
    'M.MPFUMEDZENI SECONDARY SCHOOL',
    'M.MPHAHLELE SECONDARY SCHOOL',
    'M.SEFAKAOLA SECONDARY SCHOOL',
    'MA0WANENG SECONDARY SCHOOL',
    'MAAHLAMELE SEN.SEC. SCHOOL',
    'MABARHULE SENIOR SECONDARY SC',
    'MABEA SEN.SEC SCHOOL',
    'MABOPANE HIGH SCHOOL',
    'MABOTHA HIGH SCHOOL',
    'MADADZHE SECONDARY SCHOOL',
    'MADIBO HIGH SCHOOL',
    'MADIKWENG SEN. SEC. SCHOOL',
    'MADITHAME SEN. SEC. SCHOOL',
    'MAFANNZHONI SENIOR SECONDARY',
    'MAGANDANGELE SEN.SEC SCHOOL',
    'MAGOLETSA SECONDARY SCHOOL',
    'MAGONI SECONDARY SCHOOL',
    'MAGULASAVI SECONDARY SCHOOL',
    'MAGWAGWAZA HIGH SCHOOL',
    'MAHADIKANA SECONDARY SCHOOL',
    'MAHLONTEBE SEN. SEC. SCHOOL',
    'MAHOAI SECONDARY SCHOOL',
    'MAHUDU SECONDARY SCHOOL',
    'MAHWAHWA HIGH SCHOOL',
    'MAIMANE HIGH SCHOOL',
    'MAINGANYA SECONDARY SCHOOL',
    'MAJADIBODU SEN.SEC. SCHOOL',
    'MAJEJE SECONDARY SCHOOL',
    'MAKAKAVHALE SECONDARY SCHOOL',
    'MAKANGWANE SEC SCHOOL',
    'MAKGOKA SECONDARY SCHOOL',
    'MAKOMA SECONDARY SCHOOL',
    'MAKOPI SEN. SECONDARY SCHOOL',
    'MAKOPOLE SEN.SEC. SCHOOL',
    'MAKUYA SECONDARY SCHOOL',
    'MALAMULELE HIGH SCHOOL',
    'MALATSEMOTSEPE HIGH SCHOOL',
    'MALEBO SEN SEC SCHOOL',
    'MALEBOHO SEN.SEC.SCHOOL',
    'MALEMOCHA SEC SCHOOL',
    'MALENGA SECONDARY SCHOOL',
    'MALIGANA.W. SECONDARY SCHOOL',
    'MALILELE SEN.SEC SCHOOL',
    'MALOVHANA SECONDARY SCHOOL',
    'MALUSI SEC.SCHOOL',
    'MALUTA SECONDARY SCHOOL',
    'MAMABUDUSHA SEN.SEC.SCHOOL',
    'MAMELODI SECONDARY SCHOOL',
    'MAMODIKELENG SECONDARY SCHOOL',
    'MAMOKGARI SECONDARY SCHOOL',
    'MAMVUKA SECONDARY SCHOOL',
    'MANANYE HIGH SCHOOL',
    'MANELEDZI SECONDARY SCHOOL',
    'MANG-LE-MANG SEN.SEC SCHOOL',
    'MANGWAZANA HIGH SCHOOL',
    'MANKAYANE HIGH SCHOOL',
    'MANKOENG SECONDARY SCHOOL',
    'MANOSHI SEN.SEC SCHOOL',
    'MAOKENG SEN.SEC SCHOOL',
    'MAOLWE HIGH SCHOOL',
    'MAOWANENG HIGH SCHOOL',
    'MAPHOKWANE HIGH SCHOOL',
    'MAPHUSHA HIGH SCHOOL',
    'MARIASDAL HIGH SCHOOL',
    'MARIMANE SECONDARY SCHOOL',
    'MARIPE HIGH SCHOOL',
    'MAROBATHATA HIGH SCHOOL',
    'MARUMOFASE SEN.SEC SCHOOL',
    'MASALANABO HIGH SCHOOL',
    'MASEDI HIGH SCHOOL',
    'MASEDIBU SECONDARY SCHOOL',
    'MASEMLE SECONDARY SCHOOL',
    'MASEMOLA SECONDARY SCHOOL',
    'MASERENI SECONDARY SCHOOL',
    'MASEROLE SEN. SECONDARY SCHOOL',
    'MASERUMULE SEN. SEC. SCHOOL',
    'MASHIANYANE SECONDARY SCHOOL',
    'MASHUPJE SECONDARY SCHOOL',
    'MASISEBENZE SECONDARY SCHOOL',
    'MASIZAKHE SENIOR SEC SCHOOL',
    'MASOPHA SECONDARY SCHOOL',
    'MASWIE SECONDARY SCHOOL',
    'MATAVHELA SECONDARY SCHOOL',
    'MATHEDE SECONDARY SCHOOL',
    'MATHIPA MAKGATO SEC. SCHOOL',
    'MATHOMOMAYO SEC. SCHOOL',
    'MATIME II SEN.SEC SCHOOL',
    'MATLADI TERRITORIAL H. SCHOOL',
    'MATLEBJOANE SEN.SEC. SCHOOL',
    'MATODZI SECONDARY SCHOOL',
    'MATSAMBU SECONDARY SCHOOL',
    'MATSEBONG SECONDARY SCHOOL',
    'MATSHUMANE SECONDARY SCHOOL',
    'MATSOGELLA SECONDARY SCHOOL',
    'MATSUOKWANE HIGH SCHOOL',
    'MATSWAKE SECONDARY SCHOOL',
    'MAVHUNGU.A SECONDARY SCHOOL',
    'MBABANE CENTRAL HIGH SCHOOL',
    'MBAMBISO SECONDARY SCHOOL',
    'MBILWI SECONDARY SCHOOL',
    'MDZABU SEN. SEC. SCHOOL',
    'MEADOWLANDS SECONDARY SCHOOLE',
    'MEMEZILE SECONDARY SCHOOL',
    'MHLOTSHANA SECONDARY SCHOOL',
    'MHLUZI STATE CENTRE',
    'MJOKWANE SEC. SCHOOL',
    'MKHUKHUMBA SEN. SEC. SCHOOL',
    'MMADIKANA SECONDARY SCHOOL',
    'MMAKGOBE SEN. SEC. SCHOOL',
    'MMAMETLHAKE SECONDARY SCHOOL',
    'MMANARE SECONDARY SCHOOL',
    'MMANTUTULE SECONDARY SCHOOL',
    'MMATSELA SEC.SCHOOL',
    'MMATSHIPI SEC.SCHOOL',
    'MMUTLANE SEN. SEC. SCHOOL',
    'MOCHEDI SECONDARY SCHOOL',
    'MODUMO SEN. SEC. SCHOOL',
    'MOGAKA SEN. SECONDARY SCHOOL',
    'MOGAPUTJI SECONDARY SCHOOL',
    'MOHLAKANENG SECONDARY SCHOOL',
    'MOHLAMME SENIOR SEC SCHOOL',
    'MOKHULWANE HIGH SCHOOL',
    'MOKOMENE SECONDARY SCHOOL',
    'MOKWANE SEN. SEC. SCHOOL',
    'MOROKA HIGH SCHOOL',
    'MOSHOESHOE SECONDARY SCHOOL',
    'MOSONYA HIGH SCHOOL',
    'MOTHIMAKO SECONDARY SCHOOL',
    'MOTJERE SECONDARY SCHOOL',
    'MOTODI SEN.SEC. SCHOOL',
    'MOTSEMARIA SECONDARY SCHOOL',
    'MOVHE SECONDARY SCHOOL',
    'MPANDELI SECONDARY SCHOOL',
    'MPFARISENI SECONDARY SCHOOL',
    'MPHALALENI SECONDARY SCHOOL',
    'MPHAMBO HIGH SCHOOL',
    'MPHAPHULI SECONDARY SCHOOL',
    'MPHATLALATSANE SEC. SCHOOL',
    'MPHEGO SEC SCHOOL',
    'MPHEPHHU SECONDARY SCHOOL',
    'MPHUMA SECONDARY SCHOOL',
    'MPHUMULANA SEN.SEC. SCHOOL',
    'MSHADZA SECONDARY SCHOOL',
    'MTITITI HIGH SCHOOL',
    'MUBALANGANYI SECONDARY SCHOOL',
    'MUDASWALI SECONDARY SCHOOL',
    'MUDIMELI SECONDARY SCHOOL',
    'MUDINANE SECONDARY SCHOOL',
    'MUGENA SECONDARY SCHOOL',
    'MUHANELWA SECONDARY SCHOOL',
    'MUHUYUWATHOMBA SEC. SCHOOL',
    'MUKHWATHELI SECONDARY SCHOOL',
    'MUKULA SECONDARY SCHOOL',
    'MULENGA SECONDARY SCHOOL',
    'MULIMA SECONDARY SCHOOL',
    'MUSHAATHONI SECONDARY SCHOOL',
    'MUSINA SECONDARY SCHOOL',
    'MUVHAVHA SECONDARY SCHOOL',
    'MY DARLING SEN. SEC. SCHOOL',
    'MZINONI SECONDARY SCHOOL',
    'NAKEDI SECONDARY SCHOOL',
    'NAKONKWETLOU SECONDARY SCHOOL',
    'NAPE-A-NGWATO SEN. SEC. SCHOOL',
    'NARE SEN. SEC. SCHOOL',
    'NDAEDZO SECONDARY SCHOOL',
    'NDARIENI SECONDARY SCHOOL',
    'NDHAMBI SEN. SEC. SCHOOL',
    'NGHEZIMANI SECONDARY SCHOOL',
    'NGHONYAMA SECONDARY SCHOOL',
    'NGWAABE SEN. SEC. SCHOOL',
    'NGWANA-MOHUBE SECONDARY SCHOOL',
    'NGWANAKWENA SEN.SEC. SCHOOL',
    'NGWANALLELA SECONDARY SCHOOL',
    'NGWARITSANE SECONDARY SCHOOL',
    'NIANI SECONDARY SCHOOL',
    'NKATEKO SEN. SEC. SCHOOL',
    'NKATINI SECONDARY SCHOOL',
    'NKOBO SECONDARY SCHOOL',
    'NKONENI SECONDARY SCHOOL',
    'NKOSHILO SECONDARY SCHOOL',
    'NNDAVHELESENI J.S. SCHOOL',
    'NNDITSHENI SECONDARY SCHOOL',
    'NNDWELENI SEN.SEC. SCHOOL',
    'NNGWENI SECONDARY SCHOOL',
    'NTATA SECONDARY SCHOOL',
    'NTHUBA SEN. SEC. SCHOOL',
    'NTLAGENE SEN SEC SCHOOL',
    'NTLHAVENI SECONDARY SCHOOL',
    'NTODENI SECONDARY SCHOOL',
    'NTWAMPE SEN. SEC. SCHOOL',
    'NULI RURAL GOVT SEC.SCHOOL',
    'NWANATI SECONDARY SCHOOL',
    'ODI SECONDARY SCHOOL',
    'OGWINI COMPRE. SEC. SCHOOL',
    'OMEGA EDUCATIONAL INSTITUTE',
    'ORHOVELANI SECONDARY SCHOOL',
    'Other',
    'P.RAMAANO SECONDARY SCHOOL',
    'P.T.MATLALA SECONDARY SCHOOL',
    'PABALLELO HIGH',
    'PAX INSTITUTE',
    'PEZUNGA SEN. SEC. SCHOOL',
    'PHALA HIGH SCHOOL',
    'PHANGASASA HIGH SCHOOL',
    'PHASWANA SECONDARY SCHOOL',
    'PHATAMETSANE SECONDARY SCHOOL',
    'PHATENG HIGH SCHOOL',
    'PHATEWA SNR SEC SCHOOL',
    'PHENDULANI SECONDARY SCHOOL',
    'PHILADELPHIA SECONDARY',
    'PHIRI-KOLOBE SECONDARY SCHOOL',
    'PHIRIPHIRI SECONDARY SCHOOL',
    'PHOKANOKA SECONDARY SCHOOL',
    'PHOPHI SECONDARY SCHOOL',
    'PIRWANA HIGH SCHOOL',
    'PROF.M.SHILUVANA HIGH SCHOOL',
    'PROMAT COLLEGE',
    'PUNGUTSHA SECONDARY SCHOOL',
    'R.MBULUNGENI SECONDARY SCHOOL',
    'RADIKGOMO SECONDARY SCHOOL',
    'RADIRA SEN.SECONDARY SCHOOL',
    'RAHLANGANA HIGH SCHOOL',
    'RAKGOLOKWANA HIGH SCHOOL',
    'RALELEDU SECONDARY SCHOOL',
    'RALUOMBE SECONDARY SCHOOL',
    'RALUSWIELO SECONDARY SCHOOL',
    'RALUVHIMBA SECONDARY SCHOOL',
    'RAMABELE SECONDARY SCHOOL',
    'RAMABULANA SECONDARY SCHOOL',
    'RAMASHIA SECONDARY SCHOOL',
    'RAMATAU SEN. SEC. SCHOOL',
    'RAMATEMA SECONDARY SCHOOL',
    'RAMAUBA SECONDARY SCHOOL',
    'RAMAVHOYA SECONDARY SCHOOL',
    'RAMBUDA SECONDARY SCHOOL',
    'RAMOBA HIGH SCHOOL',
    'RAMPHELANE SECONDARY SCHOOL',
    'RAMPO SECONDARY SCHOOL',
    'RAMUGONDO SECONDARY SCHOOL',
    'RANNDOGWANA SECONDARY SCHOOL',
    'RATANANG SEN.SEC.SCHOOL',
    'RATLHAHANA SECONDARY SCHOOL',
    'RATSHEPO SEN. SEC. SCHOOL',
    'RATSHIBVUMO SECONDARY SCHOOL',
    'RATSHILUMELA SECONDARY SCHOOL',
    'REFILWE SECONDARY SCHOOL',
    'RELEBOGILE SEN.SEC.SCHOOL',
    'RIBANE LAKA HIGH SCHOOL',
    'RIPAMBETA SECONDARY SCHOOL',
    'RISINGA SECONDARY SCHOOL',
    'RIVUBYE SECONDARY SCHOOL',
    'ROEDAN SCHOOL (S.A)',
    'RUSSEL BUNGENI SECONDARY',
    'S.E.COLLEGE STRENGTH IN EDU.',
    'S.MAELULA SECONDARY SCHOOL',
    'SAM MAVHINA SECONDARY SCHOOL',
    'SCHOONGEZICHT HIGH SCHOOL',
    'SEABE SECONDARY SCHOOL',
    'SEAGOTLE SECONDARY SCHOOL',
    'SEANA-MARENA HIGH SCHOOL',
    'SEBALAMAKGOLO SEC. SCHOOL',
    'SEBOYE SEN.SECONDARY SCHOOL',
    'SEFAKAOLA HIGH SCHOOL',
    'SEHLAKU SECONDARY SCHOOL',
    'SEIPHI SECONDARY SCHOOL',
    'SEKABA SECONDARY SCHOOL',
    'SEKANO-NTOANA SEC.SCHOOL',
    'SEKATE SEN.SEC.SCHOOL',
    'SEKGOPETJANA HIGH SCHOOL',
    'SEKHUKHUSA SEN.SEC.SCHOOL',
    'SEOKENG SEC SCHOOL',
    'SEOLWANA SEN.SEC. SCHOOL',
    'SERADITOLA SECONDARY SCHOOL',
    'SERIPA SEN. SEC. SCHOOL',
    'SERISHA SECONDARY SCHOOL',
    'SESHIGO SEN.SEC.SCHOOL',
    'SESHOATLHA SEN.SEC. SCHOOL',
    'SESHOKA SECONDARY SCHOOL',
    'SETLAKALANA SECONDARY SCHOOL',
    'SHANKE SECONDARY SCHOOL',
    'SHAYANDIMA SECONDARY SCHOOL',
    'SHAYINA HIGH SCHOOL',
    'SHINGUWA SECONDARY SCHOOL',
    'SHINGWEDZI SECONDARY SCHOOL',
    'SHIPUNGU SECONDARY SCHOOL',
    'SHIRILELE SECONDARY SCHOOL',
    'SHOBIYANA SEN.SEC. SCHOOL',
    'SHONDONI SECONDARY SCHOOL',
    'SHORWANE SEN. SEC. SCHOOL',
    'SIHLENGIWE SECONDARY SCHOOL',
    'SILEMALE SECONDARY SCHOOL',
    'SILOE SCHOOL FOR THE BLIND',
    'SINTHUMULE SECONDARY SCHOOL',
    'SINUGANA SECONDARY SCHOOL',
    'SITFOKOTILE SECONDARY SCHOOL',
    'SITINTILE SEN.SEC. SCHOOL',
    'SIYAMUKELA HIGH SCHOOL',
    'SOGANE SEN.SEC. SCHOOL',
    'SOMKHAHLEKWA SEC.SCHOOL',
    'SONGOZWI SECONDARY SCHOOL',
    'SOSHANGANA HIGH SCHOOL',
    'SOZAMA SECONDARY SCHOOL',
    "ST.AUGUSTINE HIGH SCHOOL",
    "ST.BEDE`S SECONDARY SCHOOL",
    "ST.BRENDAN`S SCHOOL",
    "ST.JOSEF`S HIGH SCHOOL",
    "ST.MARK`S COLLEGE",
    'SWOBANI SECONDARY SCHOOL',
    'T.DINOKO SEN. SEC. SCHOOL',
    'T.MASIAGWALA SECONDARY SCHOOL',
    'TABUDI SEN. SEC. SCHOOL',
    'TEMBISA SEN. SEC. SCHOOL',
    'THAGA-E-TALA SEN.SEC. SCHOOL',
    'THASE SECONDARY SCHOOL',
    'THATHE SECONDARY SCHOOL',
    'THE CULINARY ACADEMY',
    'THEJANE SECONDARY SCHOOL',
    'THENGWE SECONDARY SCHOOL',
    'THETHE HIGH SCHOOL',
    'THINASHAKA SECONDARY SCHOOL',
    'THOHOYANDOU SECONDARY SCHOOL',
    'THOHOYANDOU TECH. HIGH SCHOOL',
    'THULARE SECONDARY SCHOOL',
    'THUSALUSHAKA SECONDARY SCHOOL',
    'THUTO-THEBE',
    'TLADISHI SECONDARY SCHOOL',
    'TLHAKANANG SEC. SCHOOL',
    'TLOKWE SECONDARY SCHOOL',
    'TODANI SECONDARY SCHOOL',
    'TOMBOLAGOLE SECONDARY SCHOOL',
    'TONDALUSHAKA SECONDARY SCHOOL',
    'TREASURE ACADEMY',
    'TSAKANE SECONDARY SCHOOL',
    'TSAKO-THABO SECONDARY SCHOOL',
    'TSEANA SECONDARY SCHOOL',
    'TSHEBELA SSECONDARY SCHOOL',
    'TSHIANANE SECONDARY SCHOOL',
    'TSHIAWELO SECONDARY SCHOOL',
    'TSHIDIMBINI SECONDARY SCHOOL',
    'TSHIEMUEMU SECONDARY SCHOOL',
    'TSHIFHENA SECONDARY SCHOOL',
    'TSHIKHUTHULA SECONDARY SCHOOL',
    'TSHIKORORO SECONDARY SCHOOL',
    'TSHIKUNDAMALEMA SEC. SCHOOL',
    'TSHILALA SECONDARY SCHOOL',
    'TSHILAVHUTUME SECONDARY SCHOOL',
    'TSHILOGONI SECONDARY SCHOOL',
    'TSHIMBUPFE SECONDARY SCHOOL',
    'TSHINANGA SECONDARY SCHOOL',
    'TSHINAVHE SECONDARY SCHOOL',
    'TSHIPAKONI SECONDARY SCHOOL',
    'TSHIPETANE SECONDARY SCHOOL',
    'TSHIUNGULELA SECONDARY SCHOOL',
    'TSHIVHASE SECONDARY SCHOOL',
    'TSHIWANGAMATEMBELE SECONDAR.SC',
    'TSHUKUTSWE SECONDARY SCHOOL',
    'TSWAING SECONDARY SCHOOL',
    'TSWIME SECONDARY SCHOOL',
    'UNKOMAAS SECONDARY SCHOOL',
    'V.P. MANTHATA SEN.SEC. SCHOOL',
    'VASASELE SEN SECONDARY SCHOOL',
    'VELE SECONDARY SCHOOL',
    'VELELAMBEU SECONDARY SCHOOL',
    'VENDALAND TRAINING INST.',
    'VHAFAMADI SECONDARY SCHOOL',
    'VHALUVHU SECONDARY SCHOOL',
    'VHULAUDZI SECONDARY SCHOOL',
    'VHUSENDEKA SECONDARY SCHOOL',
    'VHUTAVHATSINDI SEC.SCHOOL',
    'VLAKFONTEIN TECH. HIGH SCHOOL',
    'VRYHEID ZULU SECONDARY SCHOOL',
    'VUKUZAKHE SECONDARY SCHOOL',
    'VUKUZAME SEN. SEC. SCHOOL',
    'VULI VALLEY SEN SEC SCHOOL',
    'VULIMFUNDO SECONDARY SCHOOL',
    'VUXENI SEN.SECONDARY SCHOOL',
    'W.THEMELI SECONDARY SCHOOL',
    'WALLMANSTHAL HIGH SCHOOL',
    'WATERVAL SECONDARY SCHOOL',
    'YINGWANI-RIBUNGWANI SEC.SCHOOL',
    'ZAVA HIGH SCHOOL',
    'ZENZELENI SECONDARY SCHOOL',
    'ZIBOKWANA HIGH SCHOOL',
    'ZIBUKEZULU-O-MANAYE SEC.SCHOOL',
  ];

  static const _schoolSubjects = [
    'ABRSM Practical Music',
    'Accounting',
    'Afrikaans First Add Language',
    'Afrikaans Home Language',
    'Afrikaans Second Add Language',
    'Agricultural Management Pract',
    'Agricultural Science',
    'Agricultural Technology',
    'Arabic Second Add Language',
    'Business Studies',
    'Civil Technology',
    'Computer Applications Tech',
    'Consumer Studies',
    'Dance Studies',
    'Design',
    'DiElectrical Technology',
    'Dramatic Arts',
    'Economics',
    'ElEletrical Technology',
    'Electrical Technology',
    'Engineering Graphics + Design',
    'English First Add Language',
    'English Home Language',
    'English Second Add Language',
    'Equine Studies',
    'French Second Add Language',
    'Geography',
    'German Home Language',
    'German Second Add Language',
    'Gujarati First Add Language',
    'Gujarati Home Language',
    'Gujarati Second Add Language',
    'Hebrew Second Add Language',
    'Hindi First Add Language',
    'Hindi Home Language',
    'Hindi Second Add Language',
    'History',
    'Hospitality Studies',
    'HoutbCivil Technology',
    'Information Technology',
    'IsiNdebele First Add Language',
    'IsiNdebele Home Language',
    'IsiNdebele Second Add Language',
    'IsiXhosa First Add Language',
    'IsiXhosa Home Language',
    'IsiXhosa Second Add Language',
    'IsiZulu First Add Language',
    'IsiZulu Home Language',
    'IsiZulu Second Add Language',
    'Italian Second Add Language',
    'KonstCivil Technology',
    'KrElectrical Technology',
    'Latin Second Add Language',
    'Life Orientation',
    'Life Sciences',
    'Mandarin Second Additional',
    'Marine Sciences',
    'Maritime Economics',
    'Mathematical Literacy',
    'Mathematics',
    'Mathematics (Third Paper)',
    'Mechanical Technology',
    'MoMechanical Technology',
    'Modern Greek Second Add Lang',
    'Music',
    'Nautical Science',
    'PasMechanical Technology',
    'Physical Sciences',
    'Portuguese First Add Language',
    'Portuguese Home Language',
    'Portuguese Second Add Language',
    'Religion Studies',
    'Sepedi First Add Language',
    'Sepedi Home Language',
    'Sepedi Second Add Language',
    'Sesotho First Add Language',
    'Sesotho Home Language',
    'Sesotho Second Add Language',
    'Setswana First Add Language',
    'Setswana Home Language',
    'Setswana Second Add Language',
    'SiSwati First Add Language',
    'SiSwati Home Language',
    'SiSwati Second Add Language',
    'SivieCivil Technology',
    'SpElectricall Technology',
    'Spanish Second Add Language',
    'SpeMechanical Technology',
    'SpesiCivil Technology',
    'Sport and Exercise Science',
    'SweMechanical Technology',
    'TCL Practical Grade',
    'TECHNICAL DRAWING',
    'TRAVEL AND TOURISM SG',
    'Tamil First Add Language',
    'Tamil Home Language',
    'Tamil Second Add Language',
    'Technical Methematics',
    'Technical Sciences',
    'Telegu First Add Language',
    'Telegu Home Language',
    'Telegu Second Add Language',
    'Tourism',
    'Tshivenda First Add Language',
    'Tshivenda Home Language',
    'Tshivenda Second Add Language',
    'UNISA Practical Music',
    'Urdu First Add Language',
    'Urdu Home Language',
    'Urdu Second Add Language',
    'Visual Arts',
    'Xitsonga First Add Language',
    'Xitsonga Home Language',
    'Xitsonga Second Add Language',
  ];

  static const _postalCodes = [
    '0001 - Skuilkrans Country Estate, Gauteng',
    '0002 - Glen Marais, Gauteng',
    '0003 - Hulsbosrand AH, Gauteng',
    '0015 - Bailey\'s Muckleneuk, Gauteng',
    '0024 - Mountain View, Gauteng',
    '0040 - Murrayfield, Gauteng',
    '0041 - Erasmuskloof, Gauteng',
    '0042 - Silverton, Gauteng',
    '0043 - Waltloo, Gauteng',
    '0044 - Equestria, Gauteng',
    '0050 - Pretoria Central, Gauteng',
    '0054 - Hatfield, Gauteng',
    '0055 - Lynnwood, Gauteng',
    '0059 - Menlo Park, Gauteng',
    '0060 - Brooklyn, Gauteng',
    '0061 - Queenswood, Gauteng',
    '0062 - Garsfontein, Gauteng',
    '0063 - Newlands, Gauteng',
    '0070 - Waterkloof, Gauteng',
    '0071 - Waterkloof Heights, Gauteng',
    '0072 - Waterkloof Ridge, Gauteng',
    '0073 - Wingate Park, Gauteng',
    '0074 - Pierre van Ryneveld, Gauteng',
    '0081 - Die Wilgers, Gauteng',
    '0082 - Rietondale, Gauteng',
    '0083 - Constantia Park, Gauteng',
    '0084 - Moreleta Park, Gauteng',
    '0085 - Silver Lakes, Gauteng',
    '0090 - Monument Park, Gauteng',
    '0101 - Capital Park, Gauteng',
    '0102 - Wonderboom, Gauteng',
    '0105 - Mountain View, Gauteng',
    '0109 - Gezina, Gauteng',
    '0110 - Gezina Ext, Gauteng',
    '0112 - Annlin, Gauteng',
    '0116 - Nina Park, Gauteng',
    '0118 - Danville, Gauteng',
    '0120 - Pretoria North, Gauteng',
    '0122 - Wolmer, Gauteng',
    '0125 - Sinoville, Gauteng',
    '0126 - Doornpoort, Gauteng',
    '0129 - Koedoespoort, Gauteng',
    '0130 - Magalieskruin, Gauteng',
    '0132 - Montana, Gauteng',
    '0133 - Eersterus, Gauteng',
    '0134 - Eersterust East, Gauteng',
    '0135 - Waverley, Gauteng',
    '0136 - Rietfontein, Gauteng',
    '0137 - Towerby, Gauteng',
    '0139 - Hammanskraal, Gauteng',
    '0140 - Temba, Gauteng',
    '0141 - Makapanstad, Gauteng',
    '0142 - Kekana Gardens, Gauteng',
    '0144 - Winterveld, Gauteng',
    '0145 - Hebron, Gauteng',
    '0149 - Soshanguve, Gauteng',
    '0150 - Soshanguve East, Gauteng',
    '0151 - Soshanguve South, Gauteng',
    '0152 - Mabopane, Gauteng',
    '0153 - Ga-Rankuwa, Gauteng',
    '0154 - Rosslyn, Gauteng',
    '0155 - Akasia, Gauteng',
    '0156 - Theresapark, Gauteng',
    '0157 - Karenpark, Gauteng',
    '0158 - Amandasig, Gauteng',
    '0160 - Laudium, Gauteng',
    '0161 - Erasmia, Gauteng',
    '0162 - Waterkloof Glen, Gauteng',
    '0163 - Lyttelton, Gauteng',
    '0164 - Lyttelton Manor, Gauteng',
    '0165 - Clubview, Gauteng',
    '0166 - Eldoraigne, Gauteng',
    '0167 - Pierre van Ryneveld Park, Gauteng',
    '0168 - Tiegerpoort, Gauteng',
    '0169 - Zwavelpoort, Gauteng',
    '0172 - Kameeldrift East, Gauteng',
    '0173 - Baviaanspoort, Gauteng',
    '0174 - Roodeplaat, Gauteng',
    '0180 - Cullinan, Gauteng',
    '0182 - Rayton, Gauteng',
    '0183 - Bronkhorstspruit, Gauteng',
    '0184 - Ekangala, Gauteng',
    '0185 - Zithobeni, Gauteng',
    '0186 - Delmas, Mpumalanga',
    '0190 - Centurion, Gauteng',
    '0191 - Olievenhoutbosch, Gauteng',
    '0192 - Sunderland Ridge, Gauteng',
    '0193 - Irene, Gauteng',
    '0194 - Rooihuiskraal, Gauteng',
    '0195 - The Reeds, Gauteng',
    '0196 - Croftdene, Gauteng',
    '0197 - Monaghan Farm, Gauteng',
    '0200 - Rustenburg, North West',
    '0201 - Rustenburg North, North West',
    '0202 - Kroondal, North West',
    '0203 - Boitekong, North West',
    '0204 - Phokeng, North West',
    '0205 - Mothutlung, North West',
    '0206 - Tlhabane, North West',
    '0207 - Meriting, North West',
    '0208 - Chaneng, North West',
    '0209 - Robega, North West',
    '0210 - Madikwe, North West',
    '0211 - Derdepoort, North West',
    '0212 - Swartruggens, North West',
    '0213 - Mlondolozi, North West',
    '0214 - Koster, North West',
    '0215 - Kommandonek, North West',
    '0216 - Derby, North West',
    '0217 - Reagile, North West',
    '0218 - Mooinooi, North West',
    '0219 - Modderspruit, North West',
    '0220 - Brits, North West',
    '0221 - De Wildt, North West',
    '0222 - Rethabiseng, North West',
    '0223 - Masutlhe, North West',
    '0224 - Damonsville, North West',
    '0225 - Syferkuil, North West',
    '0226 - Kgabalatsane, North West',
    '0227 - Madibogopan, North West',
    '0228 - Hebron, North West',
    '0229 - Jericho, North West',
    '0230 - Hartbeespoort, North West',
    '0231 - Melodie, North West',
    '0232 - Ifafi, North West',
    '0233 - Meerhof, North West',
    '0234 - Kosmos, North West',
    '0235 - Scotton, North West',
    '0236 - Broederstroom, North West',
    '0237 - Marikana, North West',
    '0238 - Rietfontein, North West',
    '0239 - Sefikeng, North West',
    '0240 - Bela Bela (Warmbaths), Limpopo',
    '0241 - Pienaarsrivier, Limpopo',
    '0242 - Settlers, Limpopo',
    '0243 - Alma, Limpopo',
    '0244 - Naboomspruit (Mookgophong), Limpopo',
    '0245 - Roedtan, Limpopo',
    '0246 - Mokopane (Potgietersrus), Limpopo',
    '0247 - Ga-Mphahlele, Limpopo',
    '0248 - Witrivier, Limpopo',
    '0249 - Zebediela, Limpopo',
    '0250 - Modimolle (Nylstroom), Limpopo',
    '0251 - Vaalwater, Limpopo',
    '0252 - Mabula, Limpopo',
    '0253 - Thabazimbi, Limpopo',
    '0254 - Northam, Limpopo',
    '0255 - Lephalale (Ellisras), Limpopo',
    '0256 - Stockpoort, Limpopo',
    '0257 - Alldays, Limpopo',
    '0258 - Swartwater, Limpopo',
    '0259 - Tom Burke, Limpopo',
    '0260 - Dendron, Limpopo',
    '0261 - Vivo, Limpopo',
    '0262 - Louis Trichardt, Limpopo',
    '0263 - Makhado, Limpopo',
    '0264 - Elim, Limpopo',
    '0265 - Waterval, Limpopo',
    '0266 - Malamulele, Limpopo',
    '0267 - Giyani, Limpopo',
    '0268 - Lulekani, Limpopo',
    '0269 - Phalaborwa, Limpopo',
    '0270 - Hoedspruit, Limpopo',
    '0271 - Ofcolaco, Limpopo',
    '0272 - Tzaneen, Limpopo',
    '0273 - Soekmekaar, Limpopo',
    '0274 - Bochum, Limpopo',
    '0275 - Senwabarwana, Limpopo',
    '0276 - Mokwakwaila, Limpopo',
    '0277 - Marapong, Limpopo',
    '0278 - Lephalale, Limpopo',
    '0279 - Ga-Mashashane, Limpopo',
    '0280 - Polokwane (Pietersburg), Limpopo',
    '0281 - Seshego, Limpopo',
    '0282 - Mankweng, Limpopo',
    '0283 - Moletjie, Limpopo',
    '0284 - Lebowakgomo, Limpopo',
    '0285 - Jane Furse, Limpopo',
    '0286 - Nebo, Limpopo',
    '0287 - Schuinsdraai, Limpopo',
    '0288 - Marble Hall, Limpopo',
    '0289 - Groblersdal, Limpopo',
    '0290 - Loskopdam, Mpumalanga',
    '0291 - Verena, Mpumalanga',
    '0292 - Witbank (eMalahleni), Mpumalanga',
    '0293 - Ogies, Mpumalanga',
    '0294 - Phola, Mpumalanga',
    '0295 - Hendrina, Mpumalanga',
    '0296 - Kriel, Mpumalanga',
    '0297 - Kinross, Mpumalanga',
    '0298 - Secunda, Mpumalanga',
    '0299 - Evander, Mpumalanga',
    '0300 - Trichardt, Mpumalanga',
    '0301 - Charl Cilliers, Mpumalanga',
    '0302 - Bethal, Mpumalanga',
    '0303 - Ermelo, Mpumalanga',
    '0304 - Breyten, Mpumalanga',
    '0305 - Morgenzon, Mpumalanga',
    '0306 - Davel, Mpumalanga',
    '0307 - Standerton, Mpumalanga',
    '0308 - Volksrust, Mpumalanga',
    '0309 - Perdekop, Mpumalanga',
    '0310 - Amersfoort, Mpumalanga',
    '0311 - Daggakraal, Mpumalanga',
    '0312 - Vrede, Free State',
    '0313 - Memel, Free State',
    '0314 - Reitz, Free State',
    '0315 - Tweeling, Mpumalanga',
    '0316 - Frankfort, Free State',
    '0317 - Villiers, Free State',
    '0318 - Cornelia, Free State',
    '0319 - Heilbron, Free State',
    '0320 - Coalville, Mpumalanga',
    '0321 - Kameelrivier, Mpumalanga',
    '0322 - Siyabuswa, Mpumalanga',
    '0323 - Kwaggafontein, Mpumalanga',
    '0324 - Vezubuhle, Mpumalanga',
    '0325 - eMpumalanga, Mpumalanga',
    '0326 - Tweefontein, Mpumalanga',
    '0327 - Kwamhlanga, Mpumalanga',
    '0328 - KwaNdebele, Mpumalanga',
    '0329 - Ekangala, Mpumalanga',
    '0330 - Bronkhorstspruit, Mpumalanga',
    '0331 - Sundra, Mpumalanga',
    '0332 - Leeufontein, Mpumalanga',
    '0333 - Roodeplaat, Gauteng',
    '0334 - Kameeldrift, Gauteng',
    '0335 - Cullinan, Gauteng',
    '0336 - Rayton, Gauteng',
    '0337 - Bapsfontein, Gauteng',
    '0338 - Brenthurst, Gauteng',
    '0339 - Witbank (eMalahleni), Mpumalanga',
    '0400 - Durban Central, KwaZulu-Natal',
    '0401 - Umhlanga, KwaZulu-Natal',
    '0402 - Ballito, KwaZulu-Natal',
    '0403 - Tongaat, KwaZulu-Natal',
    '0404 - Stanger (KwaDukuza), KwaZulu-Natal',
    '0405 - Gingindlovu, KwaZulu-Natal',
    '0406 - Eshowe, KwaZulu-Natal',
    '0407 - Melmoth, KwaZulu-Natal',
    '0408 - Vryheid, KwaZulu-Natal',
    '0409 - Newcastle, KwaZulu-Natal',
    '0410 - Dundee, KwaZulu-Natal',
    '0411 - Glencoe, KwaZulu-Natal',
    '0412 - Dannhauser, KwaZulu-Natal',
    '0413 - Ladysmith, KwaZulu-Natal',
    '0414 - Bergville, KwaZulu-Natal',
    '0415 - Winterton, KwaZulu-Natal',
    '0416 - Harrismith, Free State',
    '0417 - Phuthaditjhaba, Free State',
    '0418 - Clarens, Free State',
    '0419 - Ficksburg, Free State',
    '0420 - Fouriesburg, Free State',
    '0421 - Bethlehem, Free State',
    '0422 - Lindley, Free State',
    '0423 - Kroonstad, Free State',
    '0424 - Viljoenskroon, Free State',
    '0425 - Bothaville, Free State',
    '0426 - Wesselsbron, Free State',
    '0427 - Welkom, Free State',
    '0428 - Virginia, Free State',
    '0429 - Odendaalsrus, Free State',
    '0430 - Sasolburg, Free State',
    '0431 - Deneysville, Free State',
    '0432 - Vereeniging, Gauteng',
    '0433 - Vanderbijlpark, Gauteng',
    '0434 - Meyerton, Gauteng',
    '0435 - Heidelberg, Gauteng',
    '0436 - Nigel, Gauteng',
    '0437 - Springs, Gauteng',
    '0438 - Brakpan, Gauteng',
    '0439 - Boksburg, Gauteng',
    '0440 - Benoni, Gauteng',
    '0441 - Kempton Park, Gauteng',
    '0442 - Tembisa, Gauteng',
    '0443 - Olifantsfontein, Gauteng',
    '0444 - Midrand, Gauteng',
    '0445 - Halfway House, Gauteng',
    '0446 - Irene, Gauteng',
    '0447 - Lyttelton, Gauteng',
    '0448 - Verwoerdburg, Gauteng',
    '0449 - Centurion, Gauteng',
    '0450 - Pretoria, Gauteng',
    '0451 - Silverton, Gauteng',
    '0452 - Eersterus, Gauteng',
    '0453 - Mamelodi, Gauteng',
    '0454 - Atteridgeville, Gauteng',
    '0455 - Laudium, Gauteng',
    '0456 - Rosslyn, Gauteng',
    '0457 - Ga-Rankuwa, Gauteng',
    '0458 - Mabopane, Gauteng',
    '0459 - Soshanguve, Gauteng',
    '0460 - Pretoria North, Gauteng',
    '0461 - Wonderboom, Gauteng',
    '0462 - Magalieskruin, Gauteng',
    '0463 - Roodeplaat, Gauteng',
    '0464 - Cullinan, Gauteng',
    '0465 - Rayton, Gauteng',
    '0466 - Bronkhorstspruit, Gauteng',
    '0467 - Ekangala, Mpumalanga',
    '0468 - Delmas, Mpumalanga',
    '0469 - Bapsfontein, Gauteng',
    '0470 - Springs, Gauteng',
    '0471 - Nigel, Gauteng',
    '0472 - Heidelberg, Gauteng',
    '0473 - Ratanda, Gauteng',
    '0474 - Vaal Marina, Mpumalanga',
    '0475 - Deneysville, Free State',
    '0476 - Oranjeville, Free State',
    '0500 - Johannesburg Central, Gauteng',
    '0501 - Braamfontein, Gauteng',
    '0502 - Parktown, Gauteng',
    '0503 - Houghton, Gauteng',
    '0504 - Rosebank, Gauteng',
    '0505 - Sandton, Gauteng',
    '0506 - Randburg, Gauteng',
    '0507 - Roodepoort, Gauteng',
    '0508 - Krugersdorp, Gauteng',
    '0509 - Randfontein, Gauteng',
    '0510 - Westonaria, Gauteng',
    '0511 - Carletonville, Gauteng',
    '0512 - Fochville, Gauteng',
    '0513 - Oberholzer, Gauteng',
    '0514 - Soweto, Gauteng',
    '0515 - Diepkloof, Gauteng',
    '0516 - Pimville, Gauteng',
    '0517 - Klipspruit, Gauteng',
    '0518 - Naledi, Gauteng',
    '0519 - Dobsonville, Gauteng',
    '0520 - Meadowlands, Gauteng',
    '0521 - Orlando, Gauteng',
    '0522 - Jabulani, Gauteng',
    '0523 - Emdeni, Gauteng',
    '0524 - Zola, Gauteng',
    '0525 - Chiawelo, Gauteng',
    '0526 - Protea Glen, Gauteng',
    '0527 - Lenasia, Gauteng',
    '0528 - Ennerdale, Gauteng',
    '0529 - Lawley, Gauteng',
    '0530 - Orange Farm, Gauteng',
    '0531 - Finetown, Gauteng',
    '0532 - Weilers Farm, Gauteng',
    '0533 - Grasmere, Gauteng',
    '0534 - Poortjie, Gauteng',
    '0535 - Sebokeng, Gauteng',
    '0536 - Evaton, Gauteng',
    '0537 - Boipatong, Gauteng',
    '0538 - Bophelong, Gauteng',
    '0539 - Sharpeville, Gauteng',
    '0540 - Vereeniging, Gauteng',
    '0541 - Duncanville, Gauteng',
    '0542 - Arcon Park, Gauteng',
    '0543 - Vanderbijlpark, Gauteng',
    '0544 - Sasolburg, Free State',
    '0545 - Zamdela, Free State',
    '0546 - Heilbron, Free State',
    '0547 - Koppies, Free State',
    '0548 - Parys, Free State',
    '0549 - Vredefort, Free State',
    '0550 - Klerksdorp, North West',
    '0551 - Orkney, North West',
    '0552 - Stilfontein, North West',
    '0553 - Potchefstroom, North West',
    '0554 - Mafikeng, North West',
    '0555 - Zeerust, North West',
    '0556 - Groot Marico, North West',
    '0557 - Lichtenburg, North West',
    '0558 - Coligny, North West',
    '0559 - Delareyville, North West',
    '0560 - Vryburg, North West',
    '0561 - Kuruman, Northern Cape',
    '0562 - Postmasburg, Northern Cape',
    '0563 - Groblershoop, Northern Cape',
    '0564 - Upington, Northern Cape',
    '0565 - Pofadder, Northern Cape',
    '0566 - Springbok, Northern Cape',
    '0567 - Kleinzee, Northern Cape',
    '0568 - Alexander Bay, Northern Cape',
    '0569 - Port Nolloth, Northern Cape',
    '0570 - Kathu, Northern Cape',
    '0571 - Sishen, Northern Cape',
    '0572 - Hotazel, Northern Cape',
    '0573 - Van Zylsrus, Northern Cape',
    '0574 - Tsineng, Northern Cape',
    '0575 - Deben, Northern Cape',
    '0576 - Olifantshoek, Northern Cape',
    '0577 - Kimberley, Northern Cape',
    '0578 - Ritchie, Northern Cape',
    '0579 - Modderrivier, Northern Cape',
    '0580 - Barkly West, Northern Cape',
    '0581 - Delportshoop, Northern Cape',
    '0582 - Warrenton, Northern Cape',
    '0583 - Windsorton, Northern Cape',
    '0584 - Hartswater, Northern Cape',
    '0585 - Jan Kempdorp, Northern Cape',
    '0586 - Christiana, North West',
    '0587 - Bloemhof, North West',
    '0588 - Hoopstad, Free State',
    '0589 - Bultfontein, Free State',
    '0590 - Theunissen, Free State',
    '0591 - Winburg, Free State',
    '0592 - Senekal, Free State',
    '0593 - Marquard, Free State',
    '0594 - Clocolan, Free State',
    '0595 - Ladybrand, Free State',
    '0596 - Hobhouse, Free State',
    '0597 - Zastron, Free State',
    '0598 - Rouxville, Free State',
    '0599 - Smithfield, Free State',
    '0600 - Bloemfontein, Free State',
    '0601 - Heidedal, Free State',
    '0602 - Mangaung, Free State',
    '0603 - Botshabelo, Free State',
    '0604 - Thaba Nchu, Free State',
    '0605 - Dewetsdorp, Free State',
    '0606 - Wepener, Free State',
    '0607 - Van Stadensrus, Free State',
    '0608 - Wegener, Free State',
    '0609 - Reddersburg, Free State',
    '0610 - Edenburg, Free State',
    '0611 - Jagersfontein, Free State',
    '0612 - Fauresmith, Free State',
    '0613 - Petrusburg, Free State',
    '0614 - Koffiefontein, Free State',
    '0615 - Jacobsdal, Free State',
    '0616 - Philippolis, Free State',
    '0617 - Trompsburg, Free State',
    '0618 - Springfontein, Free State',
    '0619 - Bethulie, Free State',
    '0620 - Aliwal North, Eastern Cape',
    '0621 - Burgersdorp, Eastern Cape',
    '0622 - Steynsburg, Eastern Cape',
    '0623 - Molteno, Eastern Cape',
    '0624 - Sterkstroom, Eastern Cape',
    '0625 - Tarkastad, Eastern Cape',
    '0626 - Adelaide, Eastern Cape',
    '0627 - Fort Beaufort, Eastern Cape',
    '0628 - Alice, Eastern Cape',
    '0629 - Seymour, Eastern Cape',
    '0630 - Cathcart, Eastern Cape',
    '0631 - Stutterheim, Eastern Cape',
    '0632 - King William\'s Town, Eastern Cape',
    '0633 - Bhisho, Eastern Cape',
    '0634 - Berlin, Eastern Cape',
    '0635 - East London, Eastern Cape',
    '0636 - Gonubie, Eastern Cape',
    '0637 - Beacon Bay, Eastern Cape',
    '0638 - Nakana, Eastern Cape',
    '0639 - Mdantsane, Eastern Cape',
    '0640 - Dimbaza, Eastern Cape',
    '0641 - Qonce (King William\'s Town), Eastern Cape',
    '0642 - Zwelitsha, Eastern Cape',
    '0643 - Bhisho, Eastern Cape',
    '0644 - Mthatha, Eastern Cape',
    '0645 - Idutywa, Eastern Cape',
    '0646 - Willowvale, Eastern Cape',
    '0647 - Elliotdale, Eastern Cape',
    '0648 - Port St Johns, Eastern Cape',
    '0649 - Lusikisiki, Eastern Cape',
    '0650 - Flagstaff, Eastern Cape',
    '0651 - Bizana, Eastern Cape',
    '0652 - Kokstad, KwaZulu-Natal',
    '0653 - Matatiele, Eastern Cape',
    '0654 - Mount Frere, Eastern Cape',
    '0655 - Mount Ayliff, Eastern Cape',
    '0656 - Umzimkulu, KwaZulu-Natal',
    '0657 - Harding, KwaZulu-Natal',
    '0658 - Port Shepstone, KwaZulu-Natal',
    '0659 - Margate, KwaZulu-Natal',
    '0660 - St Michael\'s on Sea, KwaZulu-Natal',
    '0661 - Ramsgate, KwaZulu-Natal',
    '0662 - Southbroom, KwaZulu-Natal',
    '0663 - Port Edward, KwaZulu-Natal',
    '0664 - Umkomaas, KwaZulu-Natal',
    '0665 - Scottburgh, KwaZulu-Natal',
    '0666 - Park Rynie, KwaZulu-Natal',
    '0667 - Pennington, KwaZulu-Natal',
    '0668 - Winklespruit, KwaZulu-Natal',
    '0669 - Amanzimtoti, KwaZulu-Natal',
    '0670 - Isipingo, KwaZulu-Natal',
    '0671 - Umlazi, KwaZulu-Natal',
    '0672 - Durban South, KwaZulu-Natal',
    '0673 - Rossburgh, KwaZulu-Natal',
    '0674 - Seaview, KwaZulu-Natal',
    '0675 - Bluff, KwaZulu-Natal',
    '0676 - Mobeni, KwaZulu-Natal',
    '0677 - Jacobs, KwaZulu-Natal',
    '0678 - Clairwood, KwaZulu-Natal',
    '0679 - Mayville, KwaZulu-Natal',
    '0680 - Durban North, KwaZulu-Natal',
    '0681 - Umhlanga, KwaZulu-Natal',
    '0682 - La Lucia, KwaZulu-Natal',
    '0683 - Mount Edgecombe, KwaZulu-Natal',
    '0684 - Phoenix, KwaZulu-Natal',
    '0685 - Verulam, KwaZulu-Natal',
    '0686 - Tongaat, KwaZulu-Natal',
    '0687 - Ballito, KwaZulu-Natal',
    '0688 - Salt Rock, KwaZulu-Natal',
    '0689 - Shakaskraal, KwaZulu-Natal',
    '0690 - Stanger (KwaDukuza), KwaZulu-Natal',
    '0691 - Groutville, KwaZulu-Natal',
    '0692 - KwaMaphumulo, KwaZulu-Natal',
    '0693 - Nkwalini, KwaZulu-Natal',
    '0694 - Gingindlovu, KwaZulu-Natal',
    '0695 - Eshowe, KwaZulu-Natal',
    '0696 - Mtunzini, KwaZulu-Natal',
    '0697 - Empangeni, KwaZulu-Natal',
    '0698 - Richards Bay, KwaZulu-Natal',
    '0699 - Meerensee, KwaZulu-Natal',
    '0700 - Mpumalanga, KwaZulu-Natal',
    '0701 - Hluhluwe, KwaZulu-Natal',
    '0702 - Mtubatuba, KwaZulu-Natal',
    '0703 - St Lucia, KwaZulu-Natal',
    '0704 - Mkuze, KwaZulu-Natal',
    '0705 - Pongola, KwaZulu-Natal',
    '0706 - Piet Retief, Mpumalanga',
    '0707 - Amsterdam, Mpumalanga',
    '0708 - Wakkerstroom, Mpumalanga',
    '0709 - Mpuluzi, Mpumalanga',
    '0710 - Eerstehoek, Mpumalanga',
    '0711 - Barberton, Mpumalanga',
    '0712 - Nelspruit, Mpumalanga',
    '0713 - White River, Mpumalanga',
    '0714 - Hazyview, Mpumalanga',
    '0715 - Graskop, Mpumalanga',
    '0716 - Sabie, Mpumalanga',
    '0717 - Pilgrim\'s Rest, Mpumalanga',
    '0718 - Lydenburg (Mashishing), Mpumalanga',
    '0719 - Ohrigstad, Mpumalanga',
    '0720 - Burgersfort, Limpopo',
    '0721 - Steelpoort, Limpopo',
    '0722 - Roossenekal, Limpopo',
    '0723 - Dullstroom, Mpumalanga',
    '0724 - Machadodorp, Mpumalanga',
    '0725 - Waterval Boven, Mpumalanga',
    '0726 - Nelspruit, Mpumalanga',
    '0727 - Mataffin, Mpumalanga',
    '0728 - Nelspruit Ext, Mpumalanga',
    '0729 - Pienaar, Mpumalanga',
    '0730 - Kanyamazane, Mpumalanga',
    '0731 - KaNyamazane, Mpumalanga',
    '0732 - Kabokweni, Mpumalanga',
    '0733 - Matsulu, Mpumalanga',
    '0734 - Malelane, Mpumalanga',
    '0735 - Komatipoort, Mpumalanga',
    '0736 - Hectorspruit, Mpumalanga',
    '0737 - Kaapmuiden, Mpumalanga',
    '0738 - Nkomazi, Mpumalanga',
    '0739 - Tonga, Mpumalanga',
    '0740 - Skukuza, Mpumalanga',
    '0741 - Pretoriuskop, Mpumalanga',
    '0742 - Phalaborwa, Limpopo',
    '0743 - Gravelotte, Limpopo',
    '0744 - Letsitele, Limpopo',
    '0745 - Tzaneen, Limpopo',
    '0746 - Modjadjiskloof, Limpopo',
    '0747 - Giyani, Limpopo',
    '0748 - Malamulele, Limpopo',
    '0749 - Thohoyandou, Limpopo',
    '0750 - Mutshena, Limpopo',
    '0751 - Musina, Limpopo',
    '0752 - Beitbridge, Limpopo',
    '0753 - Madimbo, Limpopo',
    '0754 - Masisi, Limpopo',
    '0755 - Makwarela, Limpopo',
    '0756 - Sibasa, Limpopo',
    '0757 - Vuwani, Limpopo',
    '0758 - Mageva, Limpopo',
    '0759 - Nzhelele, Limpopo',
    '0760 - Vleifontein, Limpopo',
    '0761 - Tshitale, Limpopo',
    '0762 - Lwamondo, Limpopo',
    '0763 - Tshakhuma, Limpopo',
    '0764 - Waterval, Limpopo',
    '0765 - Tshitereke, Limpopo',
    '0766 - Malamulele, Limpopo',
    '0767 - Basani, Limpopo',
    '0768 - Gumbu, Limpopo',
    '0769 - Mpheni, Limpopo',
    '0770 - Louis Trichardt, Limpopo',
    '0771 - Vleifontein, Limpopo',
    '0772 - Bochum, Limpopo',
    '0773 - Senwabarwana, Limpopo',
    '0774 - Mokwakwaila, Limpopo',
    '0775 - Ga-Mphahlele, Limpopo',
    '0776 - Lebowakgomo, Limpopo',
    '0777 - Jane Furse, Limpopo',
    '0778 - Nebo, Limpopo',
    '0779 - Apel, Limpopo',
    '0780 - Marble Hall, Limpopo',
    '0781 - Motetema, Limpopo',
    '0782 - Schuinsdraai, Limpopo',
    '0783 - Groblersdal, Limpopo',
    '0784 - Loskopdam, Mpumalanga',
    '0785 - Verena, Mpumalanga',
    '0786 - eMalahleni (Witbank), Mpumalanga',
    '0787 - Ogies, Mpumalanga',
    '0788 - Phola, Mpumalanga',
    '0789 - Hendrina, Mpumalanga',
    '0790 - Kriel, Mpumalanga',
    '0791 - Kinross, Mpumalanga',
    '0792 - Secunda, Mpumalanga',
    '0793 - Evander, Mpumalanga',
    '0794 - Trichardt, Mpumalanga',
    '0795 - Bethal, Mpumalanga',
    '0796 - Ermelo, Mpumalanga',
    '0797 - Breyten, Mpumalanga',
    '0798 - Morgenzon, Mpumalanga',
    '0799 - Standerton, Mpumalanga',
    '0800 - Cape Town Central, Western Cape',
    '0801 - Table View, Western Cape',
    '0802 - Milnerton, Western Cape',
    '0803 - Bloubergrant, Western Cape',
    '0804 - Parklands, Western Cape',
    '0805 - Sunningdale, Western Cape',
    '0806 - Melkbosstrand, Western Cape',
    '0807 - Atlantis, Western Cape',
    '0808 - Mamre, Western Cape',
    '0809 - Darling, Western Cape',
    '0810 - Malmesbury, Western Cape',
    '0811 - Moorreesburg, Western Cape',
    '0812 - Vredenburg, Western Cape',
    '0813 - Langebaan, Western Cape',
    '0814 - Saldanha, Western Cape',
    '0815 - Hopefield, Western Cape',
    '0816 - Piketberg, Western Cape',
    '0817 - Porterville, Western Cape',
    '0818 - Citrusdal, Western Cape',
    '0819 - Clanwilliam, Western Cape',
    '0820 - Lamberts Bay, Western Cape',
    '0821 - Elands Bay, Western Cape',
    '0822 - Graafwater, Western Cape',
    '0823 - Vredendal, Western Cape',
    '0824 - Vanrhynsdorp, Western Cape',
    '0825 - Nieuwoudtville, Northern Cape',
    '0826 - Calvinia, Northern Cape',
    '0827 - Brandvlei, Northern Cape',
    '0828 - Kenhardt, Northern Cape',
    '0829 - Kakamas, Northern Cape',
    '0830 - Keimoes, Northern Cape',
    '0831 - Upington, Northern Cape',
    '0832 - Groblershoop, Northern Cape',
    '0833 - Griekwastad, Northern Cape',
    '0834 - Campbell, Northern Cape',
    '0835 - Douglas, Northern Cape',
    '0836 - Hopetown, Northern Cape',
    '0837 - Strydenburg, Northern Cape',
    '0838 - Britstown, Northern Cape',
    '0839 - De Aar, Northern Cape',
    '0840 - Hanover, Northern Cape',
    '0841 - Richmond, Northern Cape',
    '0842 - Colesberg, Northern Cape',
    '0843 - Norvalspont, Northern Cape',
    '0844 - Noupoort, Northern Cape',
    '0845 - Middelburg, Eastern Cape',
    '0846 - Rosmead, Eastern Cape',
    '0847 - Cradock, Eastern Cape',
    '0848 - Pearston, Eastern Cape',
    '0849 - Somerset East, Eastern Cape',
    '0850 - Cookhouse, Eastern Cape',
    '0851 - Bedford, Eastern Cape',
    '0852 - Steynsburg, Eastern Cape',
    '0853 - Molteno, Eastern Cape',
    '0854 - Sterkstroom, Eastern Cape',
    '0855 - Tarkastad, Eastern Cape',
    '0856 - Queenstown, Eastern Cape',
    '0857 - Whittlesea, Eastern Cape',
    '0858 - Sada, Eastern Cape',
    '0859 - Lesseyton, Eastern Cape',
    '0860 - Lady Frere, Eastern Cape',
    '0861 - Cala, Eastern Cape',
    '0862 - Tsomo, Eastern Cape',
    '0863 - Nqamakwe, Eastern Cape',
    '0864 - Butterworth, Eastern Cape',
    '0865 - Dutywa, Eastern Cape',
    '0866 - Mqanduli, Eastern Cape',
    '0867 - Mthatha, Eastern Cape',
    '0868 - Ngcobo, Eastern Cape',
    '0869 - Engcobo, Eastern Cape',
    '0870 - Coffimvaba, Eastern Cape',
    '0871 - Cofimvaba, Eastern Cape',
    '0872 - Idutywa, Eastern Cape',
    '0873 - Willowvale, Eastern Cape',
    '0874 - Elliotdale, Eastern Cape',
    '0875 - Port St Johns, Eastern Cape',
    '0876 - Lusikisiki, Eastern Cape',
    '0877 - Flagstaff, Eastern Cape',
    '0878 - Bizana, Eastern Cape',
    '0879 - Sterkspruit, Eastern Cape',
    '0880 - Herschel, Eastern Cape',
    '0881 - Lady Grey, Eastern Cape',
    '0882 - Barkly East, Eastern Cape',
    '0883 - Rhodes, Eastern Cape',
    '0884 - Elliot, Eastern Cape',
    '0885 - Ugie, Eastern Cape',
    '0886 - Maclear, Eastern Cape',
    '0887 - Mount Fletcher, Eastern Cape',
    '0888 - Matatiele, Eastern Cape',
    '0889 - Cedarville, Eastern Cape',
    '0890 - Mount Frere, Eastern Cape',
    '0891 - Mount Ayliff, Eastern Cape',
    '0892 - Umzimkulu, KwaZulu-Natal',
    '0893 - Harding, KwaZulu-Natal',
    '0894 - Port Shepstone, KwaZulu-Natal',
    '0895 - Margate, KwaZulu-Natal',
    '0896 - Port Edward, KwaZulu-Natal',
    '0897 - Scottburgh, KwaZulu-Natal',
    '0898 - Amanzimtoti, KwaZulu-Natal',
    '0899 - Isipingo, KwaZulu-Natal',
    '0900 - Durban, KwaZulu-Natal',
    '0901 - Berea, KwaZulu-Natal',
    '0902 - Glenwood, KwaZulu-Natal',
    '0903 - Umbilo, KwaZulu-Natal',
    '0904 - Congella, KwaZulu-Natal',
    '0905 - Mayville, KwaZulu-Natal',
    '0906 - Westville, KwaZulu-Natal',
    '0907 - Pinetown, KwaZulu-Natal',
    '0908 - New Germany, KwaZulu-Natal',
    '0909 - Kloof, KwaZulu-Natal',
    '0910 - Gillitts, KwaZulu-Natal',
    '0911 - Hillcrest, KwaZulu-Natal',
    '0912 - Botha\'s Hill, KwaZulu-Natal',
    '0913 - Assagay, KwaZulu-Natal',
    '0914 - Inchanga, KwaZulu-Natal',
    '0915 - Drummond, KwaZulu-Natal',
    '0916 - Camperdown, KwaZulu-Natal',
    '0917 - Umlaas Road, KwaZulu-Natal',
    '0918 - Pietermaritzburg, KwaZulu-Natal',
    '0919 - Mkondeni, KwaZulu-Natal',
    '0920 - Sobantu, KwaZulu-Natal',
    '0921 - Imbali, KwaZulu-Natal',
    '0922 - Edendale, KwaZulu-Natal',
    '0923 - Ashburton, KwaZulu-Natal',
    '0924 - Howick, KwaZulu-Natal',
    '0925 - Merrivale, KwaZulu-Natal',
    '0926 - Nottingham Road, KwaZulu-Natal',
    '0927 - Mooi River, KwaZulu-Natal',
    '0928 - Rosetta, KwaZulu-Natal',
    '0929 - Estcourt, KwaZulu-Natal',
    '0930 - Weenen, KwaZulu-Natal',
    '0931 - Colenso, KwaZulu-Natal',
    '0932 - Ladysmith, KwaZulu-Natal',
    '0933 - Elandslaagte, KwaZulu-Natal',
    '0934 - Van Reenen, KwaZulu-Natal',
    '0935 - Harrismith, Free State',
    '0936 - Phuthaditjhaba, Free State',
    '0937 - Clarens, Free State',
    '0938 - Fouriesburg, Free State',
    '0939 - Ficksburg, Free State',
    '0940 - Senekal, Free State',
    '0941 - Clocolan, Free State',
    '0942 - Marquard, Free State',
    '0943 - Winburg, Free State',
    '0944 - Theunissen, Free State',
    '0945 - Bultfontein, Free State',
    '0946 - Hoopstad, Free State',
    '0947 - Bothaville, Free State',
    '0948 - Wesselsbron, Free State',
    '0949 - Odendaalsrus, Free State',
    '0950 - Welkom, Free State',
    '0951 - Virginia, Free State',
    '0952 - Hennenman, Free State',
    '0953 - Ventersburg, Free State',
    '0954 - Kroonstad, Free State',
    '0955 - Viljoenskroon, Free State',
    '0956 - Orkney, North West',
    '0957 - Stilfontein, North West',
    '0958 - Klerksdorp, North West',
    '0959 - Hartbeesfontein, North West',
    '0960 - Wolmaransstad, North West',
    '0961 - Leeudoringstad, North West',
    '0962 - Makwassie, North West',
    '0963 - Schweizer-Reneke, North West',
    '0964 - Amalia, North West',
    '0965 - Vryburg, North West',
    '0966 - Stella, North West',
    '0967 - Huhudi, North West',
    '0968 - Setlagole, North West',
    '0969 - Kraaipan, North West',
    '0970 - Mafikeng, North West',
    '0971 - Mmabatho, North West',
    '0972 - Montshiwa, North West',
    '0973 - Lomanyaneng, North West',
    '0974 - Rooigrond, North West',
    '0975 - Ramatlabama, North West',
    '0976 - Morokweng, North West',
    '0977 - Tosca, North West',
    '0978 - Piet Plessis, North West',
    '0979 - Bray, North West',
    '0980 - Zeerust, North West',
    '0981 - Sannieshof, North West',
    '0982 - Ottosdal, North West',
    '0983 - Witpoort, North West',
    '0984 - Koster, North West',
    '0985 - Swartruggens, North West',
    '0986 - Rustenburg, North West',
    '0987 - Phokeng, North West',
    '0988 - Tlhabane, North West',
    '0989 - Boitekong, North West',
    '0990 - Brits, North West',
    '0991 - De Wildt, North West',
    '0992 - Hartbeespoort, North West',
    '0993 - Broederstroom, North West',
    '0994 - Mooinooi, North West',
    '0995 - Marikana, North West',
    '0996 - Kroondal, North West',
    '0997 - Rustenburg North, North West',
    '0998 - Meriting, North West',
    '0999 - Chaneng, North West',
    '1000 - Cape Town City Centre, Western Cape',
    '1001 - De Waterkant, Western Cape',
    '1002 - Green Point, Western Cape',
    '1003 - Mouille Point, Western Cape',
    '1004 - Three Anchor Bay, Western Cape',
    '1005 - Sea Point, Western Cape',
    '1006 - Fresnaye, Western Cape',
    '1007 - Bantry Bay, Western Cape',
    '1008 - Clifton, Western Cape',
    '1009 - Camps Bay, Western Cape',
    '1010 - Bakoven, Western Cape',
    '1011 - Oranjezicht, Western Cape',
    '1012 - Gardens, Western Cape',
    '1013 - Vredehoek, Western Cape',
    '1014 - Devil\'s Peak Estate, Western Cape',
    '1015 - Zonnebloem, Western Cape',
    '1016 - District Six, Western Cape',
    '1017 - Walmer Estate, Western Cape',
    '1018 - Woodstock, Western Cape',
    '1019 - Salt River, Western Cape',
    '1020 - Observatory, Western Cape',
    '1021 - Mowbray, Western Cape',
    '1022 - Rosebank, Western Cape',
    '1023 - Rondebosch, Western Cape',
    '1024 - Newlands, Western Cape',
    '1025 - Claremont, Western Cape',
    '1026 - Kenilworth, Western Cape',
    '1027 - Wynberg, Western Cape',
    '1028 - Plumstead, Western Cape',
    '1029 - Diep River, Western Cape',
    '1030 - Tokai, Western Cape',
    '1031 - Kirstenhof, Western Cape',
    '1032 - Bergvliet, Western Cape',
    '1033 - Constantia, Western Cape',
    '1034 - Hout Bay, Western Cape',
    '1035 - Llandudno, Western Cape',
    '1036 - Hout Bay Harbour, Western Cape',
    '1037 - Noordhoek, Western Cape',
    '1038 - Kommetjie, Western Cape',
    '1039 - Scarborough, Western Cape',
    '1040 - Cape Point, Western Cape',
    '1041 - Simon\'s Town, Western Cape',
    '1042 - Fish Hoek, Western Cape',
    '1043 - Kalk Bay, Western Cape',
    '1044 - Muizenberg, Western Cape',
    '1045 - St James, Western Cape',
    '1046 - Lakeside, Western Cape',
    '1047 - Retreat, Western Cape',
    '1048 - Grassy Park, Western Cape',
    '1049 - Lotus River, Western Cape',
    '1050 - Ottery, Western Cape',
    '1051 - Philippi, Western Cape',
    '1052 - Hanover Park, Western Cape',
    '1053 - Manenberg, Western Cape',
    '1054 - Gugulethu, Western Cape',
    '1055 - Nyanga, Western Cape',
    '1056 - Crossroads, Western Cape',
    '1057 - Khayelitsha, Western Cape',
    '1058 - Mitchells Plain, Western Cape',
    '1059 - Rocklands, Western Cape',
    '1060 - Lentegeur, Western Cape',
    '1061 - Portland, Western Cape',
    '1062 - Beacon Valley, Western Cape',
    '1063 - Tafelsig, Western Cape',
    '1064 - Mandalay, Western Cape',
    '1065 - Strandfontein, Western Cape',
    '1066 - Muizenberg, Western Cape',
    '1067 - Macassar, Western Cape',
    '1068 - Firgrove, Western Cape',
    '1069 - Somerset West, Western Cape',
    '1070 - Strand, Western Cape',
    '1071 - Gordon\'s Bay, Western Cape',
    '1072 - Sir Lowry\'s Pass, Western Cape',
    '1073 - Lwandle, Western Cape',
    '1074 - Nomzamo, Western Cape',
    '1075 - Grabouw, Western Cape',
    '1076 - Villiersdorp, Western Cape',
    '1077 - Franschhoek, Western Cape',
    '1078 - Paarl, Western Cape',
    '1079 - Wellington, Western Cape',
    '1080 - Mbekweni, Western Cape',
    '1081 - Simondium, Western Cape',
    '1082 - Klapmuts, Western Cape',
    '1083 - Stellenbosch, Western Cape',
    '1084 - Kylemore, Western Cape',
    '1085 - Jamestown, Western Cape',
    '1086 - Pniel, Western Cape',
    '1087 - Franschhoek, Western Cape',
    '1088 - La Motte, Western Cape',
    '1089 - Wemmershoek, Western Cape',
    '1090 - Kuilsrivier, Western Cape',
    '1091 - Brackenfell, Western Cape',
    '1092 - Kraaifontein, Western Cape',
    '1093 - Durbanville, Western Cape',
    '1094 - Bellville, Western Cape',
    '1095 - Parow, Western Cape',
    '1096 - Goodwood, Western Cape',
    '1097 - Thornton, Western Cape',
    '1098 - Edgemead, Western Cape',
    '1099 - Bothasig, Western Cape',
    '1100 - Table View, Western Cape',
    '1101 - Bloubergstrand, Western Cape',
    '1102 - Sunset Beach, Western Cape',
    '1103 - Milnerton, Western Cape',
    '1104 - Brooklyn, Western Cape',
    '1105 - Paarden Eiland, Western Cape',
    '1106 - Century City, Western Cape',
    '1107 - Montague Gardens, Western Cape',
    '1108 - Epping, Western Cape',
    '1109 - Ndabeni, Western Cape',
    '1110 - Pinelands, Western Cape',
    '1111 - Langa, Western Cape',
    '1112 - Bontcheuwel, Western Cape',
    '1113 - Crawford, Western Cape',
    '1114 - Lansdowne, Western Cape',
    '1115 - Wetton, Western Cape',
    '1116 - Sarepta, Western Cape',
    '1117 - Firlands, Western Cape',
    '1118 - Muldersvlei, Western Cape',
    '1119 - Koelenhof, Western Cape',
    '1120 - Devon Valley, Western Cape',
    '1121 - Vlottenburg, Western Cape',
    '1122 - Raithby, Western Cape',
    '1123 - Somerset West, Western Cape',
    '1124 - Vergelegen, Western Cape',
    '1125 - Macassar, Western Cape',
    '1126 - Firgrove, Western Cape',
    '1127 - Sir Lowry\'s Pass, Western Cape',
    '1128 - Gordon\'s Bay, Western Cape',
    '1129 - Strand, Western Cape',
    '1130 - Lwandle, Western Cape',
    '1131 - Nomzamo, Western Cape',
    '1132 - Grabouw, Western Cape',
    '1133 - Villiersdorp, Western Cape',
    '1134 - Worcester, Western Cape',
    '1135 - Rawsonville, Western Cape',
    '1136 - De Doorns, Western Cape',
    '1137 - Touwsrivier, Western Cape',
    '1138 - Matroosberg, Western Cape',
    '1139 - Ceres, Western Cape',
    '1140 - Prince Alfred Hamlet, Western Cape',
    '1141 - Op-die-Berg, Western Cape',
    '1142 - Wolseley, Western Cape',
    '1143 - Tulbagh, Western Cape',
    '1144 - Riebeek-Kasteel, Western Cape',
    '1145 - Riebeek West, Western Cape',
    '1146 - Malmesbury, Western Cape',
    '1147 - Moorreesburg, Western Cape',
    '1148 - Darling, Western Cape',
    '1149 - Yzerfontein, Western Cape',
    '1150 - Atlantis, Western Cape',
    '1151 - Mamre, Western Cape',
    '1152 - Kalbaskraal, Western Cape',
    '1153 - Abbotsdale, Western Cape',
    '1154 - Chatsworth, Western Cape',
    '1155 - Philadelphia, Western Cape',
    '1156 - Klipheuwel, Western Cape',
    '1157 - Saron, Western Cape',
    '1158 - Gouda, Western Cape',
    '1159 - Hermon, Western Cape',
    '1160 - Wellington, Western Cape',
    '1161 - Simondium, Western Cape',
    '1162 - Paarl, Western Cape',
    '1163 - Mbekweni, Western Cape',
    '1164 - Paarl East, Western Cape',
    '1165 - Klapmuts, Western Cape',
    '1166 - Stellenbosch, Western Cape',
    '1167 - Kylemore, Western Cape',
    '1168 - Pniel, Western Cape',
    '1169 - Jamestown, Western Cape',
    '1170 - Franschhoek, Western Cape',
    '1171 - La Motte, Western Cape',
    '1172 - Wemmershoek, Western Cape',
    '1173 - Groot Drakenstein, Western Cape',
    '1174 - Val de Vie, Western Cape',
    '1175 - Pearl Valley, Western Cape',
    '1176 - Paarl Valley, Western Cape',
    '1177 - Klein Drakenstein, Western Cape',
    '1178 - Boschendal, Western Cape',
    '1179 - Rodebosch, Western Cape',
    '1180 - Somerset West, Western Cape',
    '1181 - Strand, Western Cape',
    '1182 - Firgrove, Western Cape',
    '1183 - Lwandle, Western Cape',
    '1184 - Nomzamo, Western Cape',
    '1185 - Sir Lowry\'s Pass, Western Cape',
    '1186 - Gordon\'s Bay, Western Cape',
    '1187 - Grabouw, Western Cape',
    '1188 - Villiersdorp, Western Cape',
    '1189 - Worcester, Western Cape',
    '1190 - Rawsonville, Western Cape',
    '1191 - De Doorns, Western Cape',
    '1192 - Touwsrivier, Western Cape',
    '1193 - Ceres, Western Cape',
    '1194 - Prince Alfred Hamlet, Western Cape',
    '1195 - Op-die-Berg, Western Cape',
    '1196 - Wolseley, Western Cape',
    '1197 - Tulbagh, Western Cape',
    '1198 - Riebeek-Kasteel, Western Cape',
    '1199 - Riebeek West, Western Cape',
    '1200 - Gqeberha (Port Elizabeth), Eastern Cape',
    '1201 - Summerstrand, Eastern Cape',
    '1202 - Humewood, Eastern Cape',
    '1203 - South End, Eastern Cape',
    '1204 - Mill Park, Eastern Cape',
    '1205 - Newton Park, Eastern Cape',
    '1206 - Cotswold, Eastern Cape',
    '1207 - Kabega, Eastern Cape',
    '1208 - Hunters Retreat, Eastern Cape',
    '1209 - Linton Grange, Eastern Cape',
    '1210 - Greenacres, Eastern Cape',
    '1211 - Rowallan Park, Eastern Cape',
    '1212 - Westering, Eastern Cape',
    '1213 - Walmer, Eastern Cape',
    '1214 - Port Elizabeth Airport, Eastern Cape',
    '1215 - Deal Party, Eastern Cape',
    '1216 - Swartkops, Eastern Cape',
    '1217 - Bluewater Bay, Eastern Cape',
    '1218 - Despatch, Eastern Cape',
    '1219 - Uitenhage (Kariega), Eastern Cape',
    '1220 - KwaNobuhle, Eastern Cape',
    '1221 - Veeplaas, Eastern Cape',
    '1222 - Zwide, Eastern Cape',
    '1223 - Kwamagxaki, Eastern Cape',
    '1224 - KwaDwesi, Eastern Cape',
    '1225 - Motherwell, Eastern Cape',
    '1226 - Coega, Eastern Cape',
    '1227 - Markman, Eastern Cape',
    '1228 - Perseverance, Eastern Cape',
    '1229 - Thornhill, Eastern Cape',
    '1230 - Jeffreys Bay, Eastern Cape',
    '1231 - Paradise Beach, Eastern Cape',
    '1232 - Aston Bay, Eastern Cape',
    '1233 - Cape St Francis, Eastern Cape',
    '1234 - St Francis Bay, Eastern Cape',
    '1235 - Humansdorp, Eastern Cape',
    '1236 - Kruisfontein, Eastern Cape',
    '1237 - Patensie, Eastern Cape',
    '1238 - Hankey, Eastern Cape',
    '1239 - Loerie, Eastern Cape',
    '1240 - Addo, Eastern Cape',
    '1241 - Kirkwood, Eastern Cape',
    '1242 - Paterson, Eastern Cape',
    '1243 - Alexandria, Eastern Cape',
    '1244 - Kenton-on-Sea, Eastern Cape',
    '1245 - Boknes, Eastern Cape',
    '1246 - Port Alfred, Eastern Cape',
    '1247 - Rietriver, Eastern Cape',
    '1248 - Bathurst, Eastern Cape',
    '1249 - Grahamstown (Makhanda), Eastern Cape',
    '1250 - Fort Brown, Eastern Cape',
    '1251 - Peddie, Eastern Cape',
    '1252 - Hamburg, Eastern Cape',
    '1253 - Siyanda, Eastern Cape',
    '1254 - Bira, Eastern Cape',
    '1255 - Ngqushwa, Eastern Cape',
    '1256 - Breakfast Vlei, Eastern Cape',
    '1257 - Alexandria, Eastern Cape',
    '1258 - Paterson, Eastern Cape',
    '1259 - Addo, Eastern Cape',
    '1260 - Kirkwood, Eastern Cape',
    '1261 - Sunland, Eastern Cape',
    '1262 - Jansenville, Eastern Cape',
    '1263 - Aberdeen, Eastern Cape',
    '1264 - Graaff-Reinet, Eastern Cape',
    '1265 - Nieu-Bethesda, Eastern Cape',
    '1266 - Pearston, Eastern Cape',
    '1267 - Somerset East, Eastern Cape',
    '1268 - Cradock, Eastern Cape',
    '1269 - Tarkastad, Eastern Cape',
    '1270 - Queenstown, Eastern Cape',
    '1271 - Whittlesea, Eastern Cape',
    '1272 - Sada, Eastern Cape',
    '1273 - Lesseyton, Eastern Cape',
    '1274 - Lady Frere, Eastern Cape',
    '1275 - Cala, Eastern Cape',
    '1276 - Tsomo, Eastern Cape',
    '1277 - Nqamakwe, Eastern Cape',
    '1278 - Butterworth, Eastern Cape',
    '1279 - Dutywa, Eastern Cape',
    '1280 - Mqanduli, Eastern Cape',
    '1281 - Mthatha, Eastern Cape',
    '1282 - Ngcobo, Eastern Cape',
    '1283 - Engcobo, Eastern Cape',
    '1284 - Coffimvaba, Eastern Cape',
    '1285 - Cofimvaba, Eastern Cape',
    '1286 - Idutywa, Eastern Cape',
    '1287 - Willowvale, Eastern Cape',
    '1288 - Elliotdale, Eastern Cape',
    '1289 - Port St Johns, Eastern Cape',
    '1290 - Flagstaff, Eastern Cape',
    '1291 - Lusikisiki, Eastern Cape',
    '1292 - Bizana, Eastern Cape',
    '1293 - Sterkspruit, Eastern Cape',
    '1294 - Herschel, Eastern Cape',
    '1295 - Lady Grey, Eastern Cape',
    '1296 - Barkly East, Eastern Cape',
    '1297 - Rhodes, Eastern Cape',
    '1298 - Elliot, Eastern Cape',
    '1299 - Ugie, Eastern Cape',
  ];

  @override
  void initState() {
    super.initState();
    _floatCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _floatAnim = Tween<double>(begin: -8, end: 8).animate(
      CurvedAnimation(parent: _floatCtrl, curve: Curves.easeInOut),
    );
    _startTextReveal();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadExistingProfile());
  }

  void _loadExistingProfile() async {
    var profile = ref.read(profileProvider).valueOrNull
        ?? ref.read(authProvider).valueOrNull?.profile;
    if (profile == null) {
      // Try reading directly from Hive in case providers haven't loaded yet
      try {
        profile = await ProfileRepositoryImpl().getProfile();
      } catch (_) {}
    }
    if (profile == null) {
      // Retry once after a short delay
      await Future.delayed(const Duration(milliseconds: 500));
      profile = ref.read(profileProvider).valueOrNull
          ?? ref.read(authProvider).valueOrNull?.profile;
      if (profile == null) {
        try {
          profile = await ProfileRepositoryImpl().getProfile();
        } catch (_) {}
      }
    }
    if (profile == null) return;
    final p = profile;
    setState(() { _applyProfile(p); });
  }

  void _applyProfile(StudentProfile p) {
      _titleCtrl.text = p.personal.title;
      _initialsCtrl.text = p.personal.initials;
      _firstNameCtrl.text = p.personal.firstName;
      _lastNameCtrl.text = p.personal.lastName;
      _maidenNameCtrl.text = p.personal.maidenName;
      _gender = p.personal.gender;
      _selectedDob = p.personal.dateOfBirth;
      _idCtrl.text = p.personal.idNumber;
      _citizenship = ['SA Citizen', 'Permanent Resident', 'Foreign National']
          .contains(p.demographic.nationality)
          ? p.demographic.nationality
          : 'SA Citizen';
      _countryOfBirthCtrl.text = p.demographic.countryOfBirth;
      _homeLanguageCtrl.text = p.demographic.homeLanguage;
      _populationGroup = p.demographic.populationGroup;
      _maritalStatus = p.demographic.maritalStatus;
      _emailCtrl.text = p.contact.email;
      _phoneCtrl.text = p.contact.phone;
      _workPhoneCtrl.text = p.contact.workPhone;
      _addressCtrl.text = p.address.address;
      _addressLine2Ctrl.text = p.address.addressLine2;
      _addressLine3Ctrl.text = p.address.addressLine3;
      _province = p.address.province;
      _postalCodeCtrl.text = p.address.postalCode;
      _postalAddressCtrl.text = p.address.postalAddress;
      _postalSameAsResidential = p.address.postalAddress == p.address.address
          && p.address.postalAddress.isNotEmpty;
      _disabilityStatus = p.status.disabilityStatus;
      _bursaryRequired = p.status.bursaryRequired;
      _employmentStatus = p.status.employmentStatus;
      _schoolCtrl.text = p.school.schoolName;
      _grade = p.school.currentGrade;
      _currentlyDoing = p.school.currentlyDoing;
      _studiedPreviously = p.school.studiedPreviously;
      _subjects = p.grade12Subjects;
      _careerInterests = p.careerInterests;
      _nextOfKinNameCtrl.text = p.nextOfKin.name;
      _nextOfKinMobileCtrl.text = p.nextOfKin.mobilePhone;
      _nextOfKinHomePhoneCtrl.text = p.nextOfKin.homePhone;
      _nextOfKinWorkPhoneCtrl.text = p.nextOfKin.workPhone;
      _nextOfKinAddr1Ctrl.text = p.nextOfKin.addressLine1;
      _nextOfKinAddr2Ctrl.text = p.nextOfKin.addressLine2;
      _nextOfKinAddr3Ctrl.text = p.nextOfKin.addressLine3;
      _nextOfKinAddr4Ctrl.text = p.nextOfKin.addressLine4;
      _nextOfKinPostalCodeCtrl.text = p.nextOfKin.postalCode;
      _nextOfKinEmailCtrl.text = p.nextOfKin.email;
      _accountContactNameCtrl.text = p.accountContact.name;
      _accountContactMobileCtrl.text = p.accountContact.mobilePhone;
      _accountContactHomePhoneCtrl.text = p.accountContact.homePhone;
      _accountContactAddr1Ctrl.text = p.accountContact.addressLine1;
      _accountContactAddr2Ctrl.text = p.accountContact.addressLine2;
      _accountContactAddr3Ctrl.text = p.accountContact.addressLine3;
      _accountContactAddr4Ctrl.text = p.accountContact.addressLine4;
      _accountContactPostalCodeCtrl.text = p.accountContact.postalCode;
      _accountContactEmailCtrl.text = p.accountContact.email;
      _matricYear = p.results.matricYear;
      _applicationLevel = p.results.applicationLevel;
      _upgrading = p.results.upgrading;
      _matricType = p.results.matricType;
      _examinationNumberCtrl.text = p.results.examinationNumber;
      _schoolLeavingCertificate = p.results.schoolLeavingCertificate;
      _resultsSubjects = p.results.subjects;
      _academicYear = p.qualification.academicYear;
      if (p.qualification.choices.isNotEmpty) {
        _facultyCtrl.text = p.qualification.choices.first.faculty;
        _programmeCtrl.text = p.qualification.choices.first.programme;
      }
      _applicationPeriod = p.qualification.applicationPeriod;
      _studyMode = p.qualification.studyMode;
      _studyTiming = p.qualification.studyTiming;
      _loginPinCtrl.text = p.agreement.loginPin;
      _acceptanceStatus = p.agreement.acceptanceStatus;
      if (p.uploadedDocuments.length >= 3) {
        _uploadedFiles[0] = p.uploadedDocuments[0];
        _uploadedFiles[1] = p.uploadedDocuments[1];
        _uploadedFiles[2] = p.uploadedDocuments[2];
      }
  }

  void _startTextReveal() {
    Future.delayed(const Duration(milliseconds: 500), () {
      const total = _greetingText.length;
      const interval = Duration(milliseconds: 30);
      Timer.periodic(interval, (timer) {
        if (_visibleChars >= total || !mounted) {
          timer.cancel();
          return;
        }
        setState(() => _visibleChars += 2);
      });
    });
  }

  void _dismissGreeting() {
    setState(() => _showGreeting = false);
  }

  @override
  static Future<String?> _showSearchablePicker(BuildContext context, {
    required String title,
    required List<String> options,
    String? initialValue,
    String? Function(String)? displayTransformer,
  }) {
    return showDialog<String>(
      context: context,
      builder: (ctx) {
        final searchCtrl = TextEditingController(text: initialValue);
        final searchNode = FocusNode();
        String? selected = initialValue;
        return StatefulBuilder(
          builder: (ctx, setDialogState) {
            final filtered = options.where((o) {
              final q = searchCtrl.text.toLowerCase();
              if (q.isEmpty) return true;
              return o.toLowerCase().contains(q);
            }).toList();
            return Dialog(
              backgroundColor: AppColors.surface,
              insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 40),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                    child: TextField(
                      controller: searchCtrl,
                      focusNode: searchNode,
                      autofocus: true,
                      decoration: InputDecoration(
                        hintText: 'Search $title...',
                        prefixIcon: const Icon(Icons.search, color: AppColors.textMuted),
                        suffixIcon: searchCtrl.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear, size: 18),
                                onPressed: () {
                                  searchCtrl.clear();
                                  setDialogState(() {});
                                },
                              )
                            : null,
                      ),
                      onChanged: (_) => setDialogState(() {}),
                    ),
                  ),
                  const Divider(height: 1),
                  if (filtered.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(32),
                      child: Text('No results found', style: TextStyle(color: AppColors.textMuted)),
                    )
                  else
                    Flexible(
                      child: ListView.builder(
                        shrinkWrap: true,
                        itemCount: filtered.length,
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        itemBuilder: (_, i) {
                          final item = filtered[i];
                          final display = displayTransformer?.call(item) ?? item;
                          return ListTile(
                            dense: true,
                            selected: selected == item,
                            selectedTileColor: AppColors.primary.withValues(alpha: 0.08),
                            title: Text(display, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
                            onTap: () {
                              Navigator.pop(ctx, item);
                            },
                          );
                        },
                      ),
                    ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  void dispose() {
    _floatCtrl.dispose();
    _pageController.dispose();
    _titleCtrl.dispose();
    _initialsCtrl.dispose();
    _firstNameCtrl.dispose();
    _lastNameCtrl.dispose();
    _maidenNameCtrl.dispose();
    _idCtrl.dispose();
    _countryOfBirthCtrl.dispose();
    _homeLanguageCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _workPhoneCtrl.dispose();
    _addressCtrl.dispose();
    _addressLine2Ctrl.dispose();
    _addressLine3Ctrl.dispose();
    _postalCodeCtrl.dispose();
    _postalAddressCtrl.dispose();
    _schoolCtrl.dispose();
    _nextOfKinNameCtrl.dispose();
    _nextOfKinMobileCtrl.dispose();
    _nextOfKinHomePhoneCtrl.dispose();
    _nextOfKinWorkPhoneCtrl.dispose();
    _nextOfKinAddr1Ctrl.dispose();
    _nextOfKinAddr2Ctrl.dispose();
    _nextOfKinAddr3Ctrl.dispose();
    _nextOfKinAddr4Ctrl.dispose();
    _nextOfKinPostalCodeCtrl.dispose();
    _nextOfKinEmailCtrl.dispose();
    _accountContactNameCtrl.dispose();
    _accountContactMobileCtrl.dispose();
    _accountContactHomePhoneCtrl.dispose();
    _accountContactAddr1Ctrl.dispose();
    _accountContactAddr2Ctrl.dispose();
    _accountContactAddr3Ctrl.dispose();
    _accountContactAddr4Ctrl.dispose();
    _accountContactPostalCodeCtrl.dispose();
    _accountContactEmailCtrl.dispose();
    _examinationNumberCtrl.dispose();
    _facultyCtrl.dispose();
    _programmeCtrl.dispose();
    _loginPinCtrl.dispose();
    _schoolLeavingCertCtrl.dispose();
    super.dispose();
  }

  bool _validateCurrentPage() {
    return _formKeys[_currentPage].currentState?.validate() ?? false;
  }

  Future<void> _saveAndContinue() async {
    if (!_validateCurrentPage()) return;
    if (_currentPage < 6) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      await _saveProfile();
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _saving = true);
    try {
      final authState = ref.read(authProvider);
      final existingProfile = authState.value?.profile;
      final id = existingProfile?.id ?? const Uuid().v4();

      final profile = StudentProfile(
        id: id,
        personal: PersonalDetails(
          title: _titleCtrl.text.trim(),
          initials: _initialsCtrl.text.trim(),
          firstName: _firstNameCtrl.text.trim(),
          lastName: _lastNameCtrl.text.trim(),
          maidenName: _maidenNameCtrl.text.trim(),
          gender: _gender,
          dateOfBirth: _selectedDob,
          idNumber: _idCtrl.text.trim(),
        ),
        contact: ContactInfo(
          email: _emailCtrl.text.trim(),
          phone: _phoneCtrl.text.trim(),
          workPhone: _workPhoneCtrl.text.trim(),
        ),
        address: AddressInfo(
          address: _addressCtrl.text.trim(),
          addressLine2: _addressLine2Ctrl.text.trim(),
          addressLine3: _addressLine3Ctrl.text.trim(),
          province: _province,
          postalCode: _postalCodeCtrl.text.trim(),
          postalAddress: _postalSameAsResidential
              ? _addressCtrl.text.trim()
              : _postalAddressCtrl.text.trim(),
        ),
        demographic: DemographicInfo(
          nationality: _citizenship,
          countryOfBirth: _countryOfBirthCtrl.text.trim(),
          homeLanguage: _homeLanguageCtrl.text.trim(),
          populationGroup: _populationGroup,
          maritalStatus: _maritalStatus,
        ),
        status: StatusInfo(
          disabilityStatus: _disabilityStatus,
          bursaryRequired: _bursaryRequired,
          employmentStatus: _employmentStatus,
        ),
        school: SchoolInfo(
          schoolName: _schoolCtrl.text.trim(),
          currentGrade: _grade,
          currentlyDoing: _currentlyDoing,
          studiedPreviously: _studiedPreviously,
        ),
        nextOfKin: NextOfKin(
          name: _nextOfKinNameCtrl.text.trim(),
          mobilePhone: _nextOfKinMobileCtrl.text.trim(),
          homePhone: _nextOfKinHomePhoneCtrl.text.trim(),
          workPhone: _nextOfKinWorkPhoneCtrl.text.trim(),
          addressLine1: _nextOfKinAddr1Ctrl.text.trim(),
          addressLine2: _nextOfKinAddr2Ctrl.text.trim(),
          addressLine3: _nextOfKinAddr3Ctrl.text.trim(),
          addressLine4: _nextOfKinAddr4Ctrl.text.trim(),
          postalCode: _nextOfKinPostalCodeCtrl.text.trim(),
          email: _nextOfKinEmailCtrl.text.trim(),
        ),
        accountContact: AccountContact(
          name: _accountContactNameCtrl.text.trim(),
          mobilePhone: _accountContactMobileCtrl.text.trim(),
          homePhone: _accountContactHomePhoneCtrl.text.trim(),
          addressLine1: _accountContactAddr1Ctrl.text.trim(),
          addressLine2: _accountContactAddr2Ctrl.text.trim(),
          addressLine3: _accountContactAddr3Ctrl.text.trim(),
          addressLine4: _accountContactAddr4Ctrl.text.trim(),
          postalCode: _accountContactPostalCodeCtrl.text.trim(),
          email: _accountContactEmailCtrl.text.trim(),
        ),
        results: ResultsInfo(
          matricYear: _matricYear,
          applicationLevel: _applicationLevel,
          upgrading: _upgrading,
          matricType: _matricType,
          examinationNumber: _examinationNumberCtrl.text.trim(),
          schoolLeavingCertificate: _schoolLeavingCertificate,
          subjects: _resultsSubjects,
        ),
        qualification: QualificationInfo(
          academicYear: _academicYear,
          choices: [
            QualificationChoice(
              faculty: _facultyCtrl.text.trim(),
              programme: _programmeCtrl.text.trim(),
            ),
          ],
          applicationPeriod: _applicationPeriod,
          studyMode: _studyMode,
          studyTiming: _studyTiming,
        ),
        agreement: AgreementInfo(
          loginPin: _loginPinCtrl.text.trim(),
          acceptanceStatus: _acceptanceStatus,
        ),
        uploadedDocuments: _uploadedFiles,
        grade12Subjects: _subjects,
        careerInterests: _careerInterests,
        onboardingComplete: true,
      );

      await ref.read(profileProvider.notifier).saveProfile(profile);
      setState(() => _saving = false);
      if (mounted) context.go('/dashboard');
    } catch (e) {
      setState(() => _saving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to save profile: $e'), backgroundColor: AppColors.error),
        );
      }
    }
  }

  Widget _buildProgressBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        children: List.generate(7, (i) {
          return Expanded(
            child: Container(
              height: 4,
              margin: const EdgeInsets.symmetric(horizontal: 2),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(2),
                color: i <= _currentPage
                    ? AppColors.primary
                    : AppColors.surfaceLight,
              ),
            ),
          );
        }),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_showGreeting) {
      return GradientBackground(
        child: Scaffold(
          backgroundColor: Colors.transparent,
          body: SafeArea(
            child: GestureDetector(
              onTap: _dismissGreeting,
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 40),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AnimatedBuilder(
                        animation: _floatAnim,
                        builder: (context, child) {
                          return Transform.translate(
                            offset: Offset(0, _floatAnim.value),
                            child: child,
                          );
                        },
                        child: const StarAvatar(size: 96, pulse: true),
                      ),
                      const SizedBox(height: 40),
                      Text(
                        _greetingText.substring(0, _visibleChars.clamp(0, _greetingText.length)),
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 20,
                          height: 1.6,
                        ),
                      ),
                      const SizedBox(height: 48),
                      if (_visibleChars >= _greetingText.length)
                        ElevatedButton.icon(
                          onPressed: _dismissGreeting,
                          icon: const Icon(Icons.arrow_forward_rounded),
                          label: const Text("Let's Get Started"),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.starGold,
                            foregroundColor: Colors.black,
                            padding: const EdgeInsets.symmetric(
                                horizontal: 32, vertical: 16),
                            textStyle: const TextStyle(fontSize: 16),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      );
    }

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: const Text('Complete Your Profile'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios),
            onPressed: _currentPage > 0
                ? () => _pageController.previousPage(
                      duration: const Duration(milliseconds: 300),
                      curve: Curves.easeInOut,
                    )
                : () => context.pop(),
          ),
        ),
        body: Stack(
          children: [
            Column(
              children: [
                _buildProgressBar(),
                Text(
                  'Step ${_currentPage + 1} of 7',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: PageView(
                    controller: _pageController,
                    physics: const NeverScrollableScrollPhysics(),
                    onPageChanged: (i) => setState(() => _currentPage = i),
                    children: [
                      _buildPersonalInfo(),
                      _buildSchoolInfo(),
                      _buildSubjectsPage(),
                      _buildPreferencesPage(),
                      _buildQualificationPage(),
                      _buildAgreementPage(),
                      _buildUploadDocumentsPage(),
                    ],
                  ),
                ),
                _buildBottomButtons(),
              ],
            ),
            // Floating Star avatar
            Positioned(
              right: 16,
              bottom: 100,
              child: GestureDetector(
                onTap: _showStarHelp,
                child: AnimatedBuilder(
                  animation: _floatAnim,
                  builder: (context, child) {
                    return Transform.translate(
                      offset: Offset(0, _floatAnim.value),
                      child: child,
                    );
                  },
                  child: Container(
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.starGold.withValues(alpha: 0.4),
                          blurRadius: 12,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: const StarAvatar(size: 48, pulse: true),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showStarHelp() {
    final tips = [
      'Tell Star about yourself! Your name, ID, and contact info help universities reach you.',
      'Your school and grade info help Star recommend the right programmes.',
      'Add your Grade 12 (or Grade 11) subjects and marks so Star can calculate your APS score.',
      'Pick your interests and career goals — Star will find the best match for you!',
    ];
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            StarAvatar(size: 28),
            SizedBox(width: 8),
            Text('Star says:', style: TextStyle(color: AppColors.starGold)),
          ],
        ),
        content: Text(
          tips[_currentPage.clamp(0, tips.length - 1)],
          style: const TextStyle(color: AppColors.textPrimary, fontSize: 15, height: 1.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Got it!', style: TextStyle(color: AppColors.primaryLight)),
          ),
        ],
      ),
    );
  }

  Widget _buildPersonalInfo() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[0],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Personal Details',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text("Let's get to know you",
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            // Title + Initials
            Row(
              children: [
                Expanded(
                  flex: 2,
                  child: DropdownButtonFormField<String>(
                    value: _titleCtrl.text.isEmpty ? null : _titleCtrl.text,
                    decoration: const InputDecoration(
                      labelText: 'Title',
                      prefixIcon: Icon(Icons.badge_outlined, size: 20),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'Mr', child: Text('Mr')),
                      DropdownMenuItem(value: 'Ms', child: Text('Ms')),
                      DropdownMenuItem(value: 'Mx', child: Text('Mx')),
                      DropdownMenuItem(value: 'Dr', child: Text('Dr')),
                      DropdownMenuItem(value: 'Prof', child: Text('Prof')),
                    ],
                    onChanged: (v) => setState(() => _titleCtrl.text = v ?? ''),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 3,
                  child: TextFormField(
                    controller: _initialsCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Initials',
                        prefixIcon: Icon(Icons.short_text, size: 20)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // First + Last Name
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _firstNameCtrl,
                    decoration: const InputDecoration(
                        labelText: 'First Name',
                        prefixIcon: Icon(Icons.person_outline)),
                    validator: (v) => v?.isEmpty == true ? 'Required' : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _lastNameCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Surname',
                        prefixIcon: Icon(Icons.person_outline)),
                    validator: (v) => v?.isEmpty == true ? 'Required' : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Maiden Name (optional)
            TextFormField(
              controller: _maidenNameCtrl,
              decoration: const InputDecoration(
                labelText: 'Maiden Name (if applicable)',
                prefixIcon: Icon(Icons.person_outline),
              ),
            ),
            const SizedBox(height: 16),
            // Gender
            DropdownButtonFormField<String>(
              value: _gender.isEmpty ? null : _gender,
              decoration: const InputDecoration(
                labelText: 'Gender',
                prefixIcon: Icon(Icons.wc_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Male', child: Text('Male')),
                DropdownMenuItem(value: 'Female', child: Text('Female')),
                DropdownMenuItem(value: 'Other', child: Text('Other')),
                DropdownMenuItem(value: 'Prefer not to say', child: Text('Prefer not to say')),
              ],
              onChanged: (v) => setState(() => _gender = v ?? ''),
            ),
            const SizedBox(height: 16),
            // Date of Birth
            InkWell(
              onTap: () async {
                final picked = await showDatePicker(
                  context: context,
                  initialDate: _selectedDob ?? DateTime(2006),
                  firstDate: DateTime(1950),
                  lastDate: DateTime.now(),
                  builder: (ctx, child) => Theme(
                    data: Theme.of(context).copyWith(
                      colorScheme: const ColorScheme.dark(
                        primary: AppColors.primary,
                        surface: AppColors.surface,
                      ),
                    ),
                    child: child!,
                  ),
                );
                if (picked != null) setState(() => _selectedDob = picked);
              },
              child: InputDecorator(
                decoration: InputDecoration(
                  labelText: 'Date of Birth',
                  prefixIcon: const Icon(Icons.calendar_today_outlined),
                  suffixIcon: _selectedDob != null
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18),
                          onPressed: () => setState(() => _selectedDob = null),
                        )
                      : null,
                ),
                child: Text(
                  _selectedDob != null
                      ? '${_selectedDob!.day}/${_selectedDob!.month}/${_selectedDob!.year}'
                      : '',
                  style: const TextStyle(color: AppColors.textPrimary),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // ID Number
            TextFormField(
              controller: _idCtrl,
              decoration: const InputDecoration(
                labelText: 'ID / Passport Number',
                prefixIcon: Icon(Icons.badge_outlined),
              ),
            ),
            // --- Citizenship & Demographics ---
            const SizedBox(height: 28),
            Container(
              width: double.infinity,
              height: 1,
              color: AppColors.border,
            ),
            const SizedBox(height: 20),
            const Text('Citizenship & Demographics',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('For South African universities',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            // Citizenship
            DropdownButtonFormField<String>(
              value: _citizenship.isEmpty ? null : _citizenship,
              decoration: const InputDecoration(
                labelText: 'Citizenship Status',
                prefixIcon: Icon(Icons.flag_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'SA Citizen', child: Text('SA Citizen')),
                DropdownMenuItem(value: 'Permanent Resident', child: Text('Permanent Resident')),
                DropdownMenuItem(value: 'Foreign National', child: Text('Foreign National')),
              ],
              onChanged: (v) => setState(() => _citizenship = v ?? 'SA Citizen'),
            ),
            const SizedBox(height: 16),
            // Country of Birth
            TextFormField(
              controller: _countryOfBirthCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Country of Birth',
                prefixIcon: Icon(Icons.public_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              onTap: () async {
                final result = await _showSearchablePicker(context,
                  title: 'Country',
                  options: _countryList,
                  initialValue: _countryOfBirthCtrl.text);
                if (result != null) setState(() => _countryOfBirthCtrl.text = result);
              },
            ),
            const SizedBox(height: 16),
            // Home Language
            TextFormField(
              controller: _homeLanguageCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Home Language',
                prefixIcon: Icon(Icons.language_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              onTap: () async {
                final result = await _showSearchablePicker(context,
                  title: 'Language',
                  options: _languages,
                  initialValue: _homeLanguageCtrl.text);
                if (result != null) setState(() => _homeLanguageCtrl.text = result);
              },
            ),
            const SizedBox(height: 16),
            // Population Group
            DropdownButtonFormField<String>(
              value: _populationGroup.isEmpty ? null : _populationGroup,
              decoration: const InputDecoration(
                labelText: 'Population Group',
                prefixIcon: Icon(Icons.people_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'African', child: Text('African')),
                DropdownMenuItem(value: 'Coloured', child: Text('Coloured')),
                DropdownMenuItem(value: 'Indian/Asian', child: Text('Indian/Asian')),
                DropdownMenuItem(value: 'White', child: Text('White')),
                DropdownMenuItem(value: 'Other', child: Text('Other')),
                DropdownMenuItem(value: 'Prefer not to say', child: Text('Prefer not to say')),
              ],
              onChanged: (v) => setState(() => _populationGroup = v ?? ''),
            ),
            const SizedBox(height: 16),
            // Marital Status
            DropdownButtonFormField<String>(
              value: _maritalStatus.isEmpty ? null : _maritalStatus,
              decoration: const InputDecoration(
                labelText: 'Marital Status',
                prefixIcon: Icon(Icons.favorite_outline),
              ),
              items: const [
                DropdownMenuItem(value: 'Single', child: Text('Single')),
                DropdownMenuItem(value: 'Married', child: Text('Married')),
                DropdownMenuItem(value: 'Divorced', child: Text('Divorced')),
                DropdownMenuItem(value: 'Widowed', child: Text('Widowed')),
              ],
              onChanged: (v) => setState(() => _maritalStatus = v ?? ''),
            ),
            // --- Contact Details ---
            const SizedBox(height: 28),
            Container(
              width: double.infinity,
              height: 1,
              color: AppColors.border,
            ),
            const SizedBox(height: 20),
            const Text('Contact Details',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('How universities can reach you',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            // Email
            TextFormField(
              controller: _emailCtrl,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                labelText: 'Email Address',
                prefixIcon: Icon(Icons.email_outlined),
              ),
            ),
            const SizedBox(height: 16),
            // Cell Phone
            TextFormField(
              controller: _phoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Cell Phone Number',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
            ),
            const SizedBox(height: 16),
            // Work Phone (optional)
            TextFormField(
              controller: _workPhoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Work / Alternative Phone (optional)',
                prefixIcon: Icon(Icons.phone_forwarded_outlined),
              ),
            ),
            // --- Residential Address ---
            const SizedBox(height: 28),
            Container(
              width: double.infinity,
              height: 1,
              color: AppColors.border,
            ),
            const SizedBox(height: 20),
            const Text('Residential Address',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            const Text('Where you live',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            // Street Address
            TextFormField(
              controller: _addressCtrl,
              decoration: const InputDecoration(
                labelText: 'Street Address',
                prefixIcon: Icon(Icons.home_outlined),
              ),
            ),
            const SizedBox(height: 16),
            // Address Line 2
            TextFormField(
              controller: _addressLine2Ctrl,
              decoration: const InputDecoration(
                labelText: 'Address Line 2 (optional)',
              ),
            ),
            const SizedBox(height: 16),
            // Address Line 3
            TextFormField(
              controller: _addressLine3Ctrl,
              decoration: const InputDecoration(
                labelText: 'Street Address Line Three (Name of Town)',
              ),
            ),
            const SizedBox(height: 16),
            // Province + Postal Code
            Row(
              children: [
                Expanded(
                  flex: 3,
                  child: DropdownButtonFormField<String>(
                    value: _province.isEmpty ? null : _province,
                    decoration: const InputDecoration(
                      labelText: 'Province',
                      prefixIcon: Icon(Icons.map_outlined),
                    ),
                    items: AppConstants.provinces
                        .map((p) => DropdownMenuItem(value: p, child: Text(p)))
                        .toList(),
                    onChanged: (v) => setState(() => _province = v ?? ''),
                    validator: (v) => v == null ? 'Select your province' : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: TextFormField(
                    controller: _postalCodeCtrl,
                    readOnly: true,
                    decoration: const InputDecoration(
                      labelText: 'Postal Code',
                      prefixIcon: Icon(Icons.pin_outlined),
                      suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
                    ),
                    onTap: () async {
                      final result = await _showSearchablePicker(context,
                        title: 'Postal Code',
                        options: _postalCodes,
                        initialValue: _postalCodeCtrl.text,
                        displayTransformer: (p) => p);
                      if (result != null) {
                        setState(() => _postalCodeCtrl.text = result.split(' - ').first.trim());
                      }
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Postal Address
            TextFormField(
              controller: _postalAddressCtrl,
              enabled: !_postalSameAsResidential,
              decoration: InputDecoration(
                labelText: 'Postal Address',
                prefixIcon: const Icon(Icons.mail_outlined),
                suffixIcon: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    GestureDetector(
                      onTap: () => setState(() {
                        _postalSameAsResidential = !_postalSameAsResidential;
                        if (_postalSameAsResidential) {
                          _postalAddressCtrl.clear();
                        }
                      }),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('Same',
                                style: TextStyle(
                                    fontSize: 11,
                                    color: _postalSameAsResidential
                                        ? AppColors.primaryLight
                                        : AppColors.textSecondary)),
                            Icon(
                              _postalSameAsResidential
                                  ? Icons.check_box
                                  : Icons.check_box_outline_blank,
                              size: 18,
                              color: _postalSameAsResidential
                                  ? AppColors.primaryLight
                                  : AppColors.textSecondary,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            // --- Additional Info ---
            const SizedBox(height: 28),
            Container(
              width: double.infinity,
              height: 1,
              color: AppColors.border,
            ),
            const SizedBox(height: 20),
            const Text('Additional Information',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            // Disability
            DropdownButtonFormField<String>(
              value: _disabilityStatus.isEmpty ? null : _disabilityStatus,
              decoration: const InputDecoration(
                labelText: 'Do you have a disability?',
                prefixIcon: Icon(Icons.accessible_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'No', child: Text('No')),
                DropdownMenuItem(value: 'Yes, physical', child: Text('Yes, physical')),
                DropdownMenuItem(value: 'Yes, visual', child: Text('Yes, visual')),
                DropdownMenuItem(value: 'Yes, hearing', child: Text('Yes, hearing')),
                DropdownMenuItem(value: 'Yes, learning', child: Text('Yes, learning')),
                DropdownMenuItem(value: 'Yes, other', child: Text('Yes, other')),
                DropdownMenuItem(value: 'Prefer not to say', child: Text('Prefer not to say')),
              ],
              onChanged: (v) => setState(() => _disabilityStatus = v ?? ''),
            ),
            const SizedBox(height: 16),
            // Bursary Required
            DropdownButtonFormField<String>(
              value: _bursaryRequired.isEmpty ? null : _bursaryRequired,
              decoration: const InputDecoration(
                labelText: 'Do you require a bursary?',
                prefixIcon: Icon(Icons.monetization_on_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Yes', child: Text('Yes')),
                DropdownMenuItem(value: 'No', child: Text('No')),
                DropdownMenuItem(value: 'Unsure', child: Text('Unsure')),
              ],
              onChanged: (v) => setState(() => _bursaryRequired = v ?? ''),
            ),
            const SizedBox(height: 16),
            // Employment Status
            DropdownButtonFormField<String>(
              value: _employmentStatus.isEmpty ? null : _employmentStatus,
              decoration: const InputDecoration(
                labelText: 'Employment Status',
                prefixIcon: Icon(Icons.work_outline),
              ),
              items: const [
                DropdownMenuItem(value: 'Unemployed', child: Text('Unemployed')),
                DropdownMenuItem(value: 'Employed (part-time)', child: Text('Employed (part-time)')),
                DropdownMenuItem(value: 'Employed (full-time)', child: Text('Employed (full-time)')),
                DropdownMenuItem(value: 'Self-employed', child: Text('Self-employed')),
              ],
              onChanged: (v) => setState(() => _employmentStatus = v ?? ''),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildSchoolInfo() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[1],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Next of Kin Details ──
            const _SectionHeader(title: 'Next of Kin Details'),
            const SizedBox(height: 16),
            const Text('Personal and Contact Information',
                style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            TextFormField(
              controller: _nextOfKinNameCtrl,
              decoration: const InputDecoration(
                labelText: 'Name(s) *',
                prefixIcon: Icon(Icons.person_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinMobileCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Mobile/Cellular Phone Number *',
                prefixIcon: Icon(Icons.phone_android_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinHomePhoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Home Phone Number *',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinWorkPhoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Work Phone Number',
                prefixIcon: Icon(Icons.business_outlined),
              ),
            ),
            const SizedBox(height: 20),
            const Text('Address Information',
                style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            TextFormField(
              controller: _nextOfKinAddr1Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 1 *',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinAddr2Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 2 *',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinAddr3Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 3',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinAddr4Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 4',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinPostalCodeCtrl,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Postal Code *',
                prefixIcon: Icon(Icons.pin_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _nextOfKinEmailCtrl,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                labelText: 'Email Address *',
                prefixIcon: Icon(Icons.email_outlined),
              ),
              validator: (v) {
                if (v?.trim().isEmpty == true) return 'Required';
                if (!v!.contains('@')) return 'Enter a valid email';
                return null;
              },
            ),

            const SizedBox(height: 32),

            // ── Account Contact Details ──
            const _SectionHeader(title: 'Account Contact Details'),
            const SizedBox(height: 16),
            const Text('Account Contact Information',
                style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            TextFormField(
              controller: _accountContactNameCtrl,
              decoration: const InputDecoration(
                labelText: 'Name(s) *',
                prefixIcon: Icon(Icons.person_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _accountContactMobileCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Mobile/Cellular Phone Number *',
                prefixIcon: Icon(Icons.phone_android_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _accountContactHomePhoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Home Phone Number *',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 20),
            const Text('Address Information',
                style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            TextFormField(
              controller: _accountContactAddr1Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 1 *',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _accountContactAddr2Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 2 *',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _accountContactAddr3Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 3',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _accountContactAddr4Ctrl,
              decoration: const InputDecoration(
                labelText: 'Postal Address Line 4',
                prefixIcon: Icon(Icons.location_on_outlined),
              ),
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _accountContactPostalCodeCtrl,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Postal Code *',
                prefixIcon: Icon(Icons.pin_outlined),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            TextFormField(
              controller: _accountContactEmailCtrl,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                labelText: 'Email Address *',
                prefixIcon: Icon(Icons.email_outlined),
              ),
              validator: (v) {
                if (v?.trim().isEmpty == true) return 'Required';
                if (!v!.contains('@')) return 'Enter a valid email';
                return null;
              },
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildSubjectsPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[2],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Results Details'),
            const SizedBox(height: 16),
            // Matric Year
            DropdownButtonFormField<int>(
              value: _matricYear == 0 ? null : _matricYear,
              decoration: const InputDecoration(
                labelText: 'Matric/Grade 12 Year (YYYY) *',
                prefixIcon: Icon(Icons.calendar_today_outlined),
              ),
              items: List.generate(31, (i) => 2000 + i)
                  .map((y) => DropdownMenuItem(value: y, child: Text('$y')))
                  .toList(),
              onChanged: (v) => setState(() => _matricYear = v ?? 0),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Undergraduate / Postgraduate
            DropdownButtonFormField<String>(
              value: _applicationLevel.isEmpty ? null : _applicationLevel,
              decoration: const InputDecoration(
                labelText: 'Applying for Undergraduate or Postgraduate? *',
                prefixIcon: Icon(Icons.school_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Undergraduate', child: Text('Undergraduate')),
                DropdownMenuItem(value: 'Postgraduate', child: Text('Postgraduate')),
              ],
              onChanged: (v) => setState(() => _applicationLevel = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Upgrading
            DropdownButtonFormField<String>(
              value: _upgrading.isEmpty ? null : _upgrading,
              decoration: const InputDecoration(
                labelText: 'Are you Upgrading? *',
                prefixIcon: Icon(Icons.refresh_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Yes', child: Text('Yes')),
                DropdownMenuItem(value: 'No', child: Text('No')),
              ],
              onChanged: (v) => setState(() => _upgrading = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Matric Type
            DropdownButtonFormField<String>(
              value: _matricType.isEmpty ? null : _matricType,
              decoration: const InputDecoration(
                labelText: 'Completing/Completed South African or International Matric *',
                prefixIcon: Icon(Icons.public_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'South African', child: Text('South African')),
                DropdownMenuItem(value: 'International', child: Text('International')),
              ],
              onChanged: (v) => setState(() => _matricType = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Examination Number
            TextFormField(
              controller: _examinationNumberCtrl,
              decoration: const InputDecoration(
                labelText: 'Matric/Grade 12 Examination Number',
                prefixIcon: Icon(Icons.numbers_outlined),
              ),
            ),
            const SizedBox(height: 14),
            // School Leaving Certificate
            TextFormField(
              controller: _schoolLeavingCertCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Final School Leaving Certificate *',
                prefixIcon: Icon(Icons.verified_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                const certs = ['Cert of Complete Exemption', 'GRADE 12', 'NTC3/N3/NSC'];
                final result = await _showSearchablePicker(context,
                  title: 'Certificate',
                  options: certs,
                  initialValue: _schoolLeavingCertificate);
                if (result != null) setState(() => _schoolLeavingCertificate = result);
              },
            ),

            const SizedBox(height: 24),
            const Text('Subject Details (Repeated Entry List)',
                style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            // Subject list
            ..._resultsSubjects.asMap().entries.map((entry) {
              final i = entry.key;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: DropdownButtonFormField<String>(
                        value: _resultsSubjects[i].subject.isEmpty
                            ? null
                            : _resultsSubjects[i].subject,
                        decoration: const InputDecoration(
                          labelText: 'Subject *',
                          contentPadding:
                              EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                        ),
                        items: _schoolSubjects
                            .map((s) => DropdownMenuItem(
                                value: s,
                                child: Text(s,
                                    style: const TextStyle(fontSize: 12))))
                            .toList(),
                        onChanged: (v) {
                          if (v != null) {
                            setState(() => _resultsSubjects[i] =
                                _resultsSubjects[i].copyWith(subject: v));
                          }
                        },
                        validator: (v) => v == null ? 'Required' : null,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      flex: 1,
                      child: DropdownButtonFormField<String>(
                        value: _resultsSubjects[i].grade.isEmpty
                            ? null
                            : _resultsSubjects[i].grade,
                        decoration: const InputDecoration(
                          labelText: 'Grade *',
                          contentPadding:
                              EdgeInsets.symmetric(horizontal: 6, vertical: 10),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'NOT ACHIEVED', child: Text('NOT ACHIEVED', style: TextStyle(fontSize: 11))),
                          DropdownMenuItem(value: 'ELEMENTARY ACHIEVEMENT', child: Text('ELEMENTARY ACHIEVEMENT', style: TextStyle(fontSize: 11))),
                          DropdownMenuItem(value: 'MODERATE ACHIEVEMENT', child: Text('MODERATE ACHIEVEMENT', style: TextStyle(fontSize: 11))),
                          DropdownMenuItem(value: 'ADEQUATE ACHIEVEMENT', child: Text('ADEQUATE ACHIEVEMENT', style: TextStyle(fontSize: 11))),
                          DropdownMenuItem(value: 'SUBSTANTIAL ACHIEVEMENT', child: Text('SUBSTANTIAL ACHIEVEMENT', style: TextStyle(fontSize: 11))),
                          DropdownMenuItem(value: 'MERITORIUS ACHIEVEMENT', child: Text('MERITORIUS ACHIEVEMENT', style: TextStyle(fontSize: 11))),
                          DropdownMenuItem(value: 'OUTSTANDING ACHIEVEMENT', child: Text('OUTSTANDING ACHIEVEMENT', style: TextStyle(fontSize: 11))),
                          DropdownMenuItem(value: 'NSC', child: Text('NSC', style: TextStyle(fontSize: 11))),
                        ],
                        onChanged: (v) {
                          if (v != null) {
                            setState(() => _resultsSubjects[i] =
                                _resultsSubjects[i].copyWith(grade: v));
                          }
                        },
                        validator: (v) => v == null ? 'Required' : null,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      flex: 1,
                      child: DropdownButtonFormField<int>(
                        value: _resultsSubjects[i].result.isEmpty
                            ? null
                            : int.tryParse(_resultsSubjects[i].result),
                        decoration: const InputDecoration(
                          labelText: 'Level',
                          contentPadding:
                              EdgeInsets.symmetric(horizontal: 6, vertical: 10),
                        ),
                        items: List.generate(7, (i) => i + 1)
                            .map((l) => DropdownMenuItem(
                                value: l,
                                child: Text('$l',
                                    style: const TextStyle(fontSize: 12))))
                            .toList(),
                        onChanged: (v) {
                          if (v != null) {
                            setState(() => _resultsSubjects[i] =
                                _resultsSubjects[i].copyWith(result: '$v'));
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      flex: 1,
                      child: TextFormField(
                        initialValue: _resultsSubjects[i].symbol,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: '% *',
                          contentPadding:
                              EdgeInsets.symmetric(horizontal: 6, vertical: 10),
                        ),
                        onChanged: (v) {
                          setState(() => _resultsSubjects[i] =
                              _resultsSubjects[i].copyWith(symbol: v));
                        },
                        validator: (v) =>
                            v?.trim().isEmpty == true ? 'Required' : null,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.remove_circle_outline,
                          color: AppColors.error, size: 20),
                      onPressed: () =>
                          setState(() => _resultsSubjects.removeAt(i)),
                    ),
                  ],
                ),
              );
            }),
            OutlinedButton.icon(
              onPressed: () {
                setState(() => _resultsSubjects
                    .add(const SubjectDetail()));
              },
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Add Subject'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.primaryLight,
                side: const BorderSide(color: AppColors.border),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildPreferencesPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[3],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Educational Institution Details'),
            const SizedBox(height: 16),
            const Text('School Details',
                style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            TextFormField(
              controller: _schoolCtrl,
              readOnly: true,
              decoration: const InputDecoration(
                labelText: 'Which school did you attend last? *',
                prefixIcon: Icon(Icons.school_outlined),
                suffixIcon: Icon(Icons.arrow_drop_down, color: AppColors.textMuted),
              ),
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
              onTap: () async {
                final result = await _showSearchablePicker(context,
                  title: 'School',
                  options: _schoolList,
                  initialValue: _schoolCtrl.text);
                if (result != null) setState(() => _schoolCtrl.text = result);
              },
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              value: _currentlyDoing.isEmpty ? null : _currentlyDoing,
              decoration: const InputDecoration(
                labelText: 'What are you currently doing? *',
                prefixIcon: Icon(Icons.work_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Studying at school', child: Text('Studying at school')),
                DropdownMenuItem(value: 'Studying at tertiary institution', child: Text('Studying at tertiary institution')),
                DropdownMenuItem(value: 'Working', child: Text('Working')),
                DropdownMenuItem(value: 'Gap Year', child: Text('Gap Year')),
                DropdownMenuItem(value: 'Unemployed', child: Text('Unemployed')),
                DropdownMenuItem(value: 'Other', child: Text('Other')),
              ],
              onChanged: (v) => setState(() => _currentlyDoing = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 24),
            const Text('Other Tertiary Institution Details',
                style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _studiedPreviously.isEmpty ? null : _studiedPreviously,
              decoration: const InputDecoration(
                labelText: 'Have you studied at another institution previously? *',
                prefixIcon: Icon(Icons.account_balance_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'Yes', child: Text('Yes')),
                DropdownMenuItem(value: 'No', child: Text('No')),
              ],
              onChanged: (v) => setState(() => _studiedPreviously = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildQualificationPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[4],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Qualification Details'),
            const SizedBox(height: 16),
            // Academic Year
            DropdownButtonFormField<int>(
              value: _academicYear == 0 ? null : _academicYear,
              decoration: const InputDecoration(
                labelText: 'Academic Year *',
                prefixIcon: Icon(Icons.calendar_today_outlined),
              ),
              items: List.generate(6, (i) => DateTime.now().year + i)
                  .map((y) => DropdownMenuItem(value: y, child: Text('$y')))
                  .toList(),
              onChanged: (v) => setState(() => _academicYear = v ?? 0),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Faculty/School
            DropdownButtonFormField<String>(
              value: _facultyCtrl.text.isEmpty ? null : _facultyCtrl.text,
              decoration: const InputDecoration(
                labelText: 'Limit your selection to a specific Faculty/School *',
                prefixIcon: Icon(Icons.school_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'HEALTH SCIENCES', child: Text('HEALTH SCIENCES')),
                DropdownMenuItem(value: 'HUMANITIES, SOCIAL SCIENCES AN', child: Text('HUMANITIES, SOCIAL SCIENCES AN')),
                DropdownMenuItem(value: 'MANAGEMENT, COMMERC', child: Text('MANAGEMENT, COMMERC')),
                DropdownMenuItem(value: 'SCIENCE, ENGINEERING AND AGRIC', child: Text('SCIENCE, ENGINEERING AND AGRIC')),
              ],
              onChanged: (v) => setState(() => _facultyCtrl.text = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Programme
            DropdownButtonFormField<String>(
              value: _programmeCtrl.text.isEmpty ? null : _programmeCtrl.text,
              decoration: const InputDecoration(
                labelText: 'Choose a programme *',
                prefixIcon: Icon(Icons.auto_stories_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'HSBAMS', child: Text('HSBAMS - BA (MEDIA STUDIES)')),
                DropdownMenuItem(value: 'HSBADS', child: Text('HSBADS - BA IN DEVELOPMENT STUDIES')),
                DropdownMenuItem(value: 'HSBAIR', child: Text('HSBAIR - BA IN INTERNATIONAL RELATIONS')),
                DropdownMenuItem(value: 'HSBALP', child: Text('HSBALP - BA IN LANGUAGE PRACTICE')),
                DropdownMenuItem(value: 'HSBAYD', child: Text('HSBAYD - BA IN YOUTH DEVELOPMENT')),
                DropdownMenuItem(value: 'SEBECP', child: Text('SEBECP - BACHELOR OF EDUCATION IN SENIOR PHASE')),
                DropdownMenuItem(value: 'SEBELP', child: Text('SEBELP - BACHELOR OF EDUCATION IN SENIOR PHASE')),
                DropdownMenuItem(value: 'SEBESP', child: Text('SEBESP - BACHELOR OF EDUCATION IN SENIOR PHASE')),
                DropdownMenuItem(value: 'HSBBA', child: Text('HSBBA - BACHELOR OF ARTS')),
                DropdownMenuItem(value: 'HSBAEL', child: Text('HSBAEL - BACHELOR OF ARTS (ENGLISH LANG AND LIT)')),
                DropdownMenuItem(value: 'HSBBAH', child: Text('HSBBAH - BACHELOR OF ARTS HISTORY STREAM')),
                DropdownMenuItem(value: 'SEBEFP', child: Text('SEBEFP - BACHELOR OF EDUCATION IN FOUNDATION PHAS')),
                DropdownMenuItem(value: 'HSBIKA', child: Text('HSBIKA - BACHELOR OF INDIGENOUS KNOWLEDGE SYSTEMS')),
                DropdownMenuItem(value: 'HSBIKC', child: Text('HSBIKC - BACHELOR OF INDIGENOUS KNOWLEDGE SYSTEMS')),
                DropdownMenuItem(value: 'HSBIKH', child: Text('HSBIKH - BACHELOR OF INDIGENOUS KNOWLEDGE SYSTEMS')),
                DropdownMenuItem(value: 'HSBIKS', child: Text('HSBIKS - BACHELOR OF INDIGENOUS KNOWLEDGE SYSTEMS')),
                DropdownMenuItem(value: 'HSBBSW', child: Text('HSBBSW - BACHELOR OF SOCIAL WORK')),
                DropdownMenuItem(value: 'HSBBT', child: Text('HSBBT - BACHELOR OF THEOLOGY')),
                DropdownMenuItem(value: 'HSCCCS', child: Text('HSCCCS - HIGHER CERTIFICATE IN CHORAL STUDIES')),
                DropdownMenuItem(value: 'HSCHCM', child: Text('HSCHCM - HIGHER CERTIFICATE IN MUSIC')),
                DropdownMenuItem(value: 'HSBDAS', child: Text('HSBDAS - PGDIP IN AFRICAN STUDIES')),
                DropdownMenuItem(value: 'HSBDGS', child: Text('HSBDGS - PGDIP IN GENDER STUDIES')),
                DropdownMenuItem(value: 'SEPGCE', child: Text('SEPGCE - POSTGRADUATE CERTIFICATE IN EDUCATION')),
              ],
              onChanged: (v) => setState(() => _programmeCtrl.text = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Application Period
            DropdownButtonFormField<String>(
              value: _applicationPeriod.isEmpty ? null : _applicationPeriod,
              decoration: const InputDecoration(
                labelText: 'For which period are you applying? *',
                prefixIcon: Icon(Icons.date_range_outlined),
              ),
              items: const [
                DropdownMenuItem(value: '1ST YEAR', child: Text('1ST YEAR')),
              ],
              onChanged: (v) => setState(() => _applicationPeriod = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Study Mode
            DropdownButtonFormField<String>(
              value: _studyMode.isEmpty ? null : _studyMode,
              decoration: const InputDecoration(
                labelText: 'How would you like to study for this programme? *',
                prefixIcon: Icon(Icons.school_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'FULL-TIME', child: Text('FULL-TIME')),
              ],
              onChanged: (v) => setState(() => _studyMode = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 14),
            // Study Timing
            DropdownButtonFormField<String>(
              value: _studyTiming.isEmpty ? null : _studyTiming,
              decoration: const InputDecoration(
                labelText: 'When would you like to study for the qualification? *',
                prefixIcon: Icon(Icons.access_time_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'YEAR', child: Text('YEAR')),
              ],
              onChanged: (v) => setState(() => _studyTiming = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildAgreementPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[5],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Rules and Agreement'),
            const SizedBox(height: 16),
            const Text(
              'Before continuing, please review and accept the terms.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: _loginPinCtrl,
              decoration: const InputDecoration(
                labelText: 'Login Pin Number *',
                prefixIcon: Icon(Icons.lock_outline),
              ),
              keyboardType: TextInputType.number,
              obscureText: true,
              validator: (v) => v?.trim().isEmpty == true ? 'Required' : null,
            ),
            const SizedBox(height: 20),
            DropdownButtonFormField<String>(
              value: _acceptanceStatus.isEmpty ? null : _acceptanceStatus,
              decoration: const InputDecoration(
                labelText: 'Acceptance Status *',
                prefixIcon: Icon(Icons.assignment_turned_in_outlined),
              ),
              items: const [
                DropdownMenuItem(value: 'I Accept', child: Text('I Accept')),
                DropdownMenuItem(value: 'I do not Accept', child: Text('I do not Accept')),
              ],
              onChanged: (v) => setState(() => _acceptanceStatus = v ?? ''),
              validator: (v) => v == null ? 'Required' : null,
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Future<void> _saveCurrentPage() async {
    setState(() => _saving = true);
    try {
      final authState = ref.read(authProvider);
      final existingProfile = authState.value?.profile;
      final id = existingProfile?.id ?? const Uuid().v4();

      final profile = StudentProfile(
        id: id,
        personal: PersonalDetails(
          title: _titleCtrl.text.trim(),
          initials: _initialsCtrl.text.trim(),
          firstName: _firstNameCtrl.text.trim(),
          lastName: _lastNameCtrl.text.trim(),
          maidenName: _maidenNameCtrl.text.trim(),
          gender: _gender,
          dateOfBirth: _selectedDob,
          idNumber: _idCtrl.text.trim(),
        ),
        contact: ContactInfo(
          email: _emailCtrl.text.trim(),
          phone: _phoneCtrl.text.trim(),
          workPhone: _workPhoneCtrl.text.trim(),
        ),
        address: AddressInfo(
          address: _addressCtrl.text.trim(),
          addressLine2: _addressLine2Ctrl.text.trim(),
          addressLine3: _addressLine3Ctrl.text.trim(),
          province: _province,
          postalCode: _postalCodeCtrl.text.trim(),
          postalAddress: _postalSameAsResidential
              ? _addressCtrl.text.trim()
              : _postalAddressCtrl.text.trim(),
        ),
        demographic: DemographicInfo(
          nationality: _citizenship,
          countryOfBirth: _countryOfBirthCtrl.text.trim(),
          homeLanguage: _homeLanguageCtrl.text.trim(),
          populationGroup: _populationGroup,
          maritalStatus: _maritalStatus,
        ),
        status: StatusInfo(
          disabilityStatus: _disabilityStatus,
          bursaryRequired: _bursaryRequired,
          employmentStatus: _employmentStatus,
        ),
        school: SchoolInfo(
          schoolName: _schoolCtrl.text.trim(),
          currentGrade: _grade,
          currentlyDoing: _currentlyDoing,
          studiedPreviously: _studiedPreviously,
        ),
        nextOfKin: NextOfKin(
          name: _nextOfKinNameCtrl.text.trim(),
          mobilePhone: _nextOfKinMobileCtrl.text.trim(),
          homePhone: _nextOfKinHomePhoneCtrl.text.trim(),
          workPhone: _nextOfKinWorkPhoneCtrl.text.trim(),
          addressLine1: _nextOfKinAddr1Ctrl.text.trim(),
          addressLine2: _nextOfKinAddr2Ctrl.text.trim(),
          addressLine3: _nextOfKinAddr3Ctrl.text.trim(),
          addressLine4: _nextOfKinAddr4Ctrl.text.trim(),
          postalCode: _nextOfKinPostalCodeCtrl.text.trim(),
          email: _nextOfKinEmailCtrl.text.trim(),
        ),
        accountContact: AccountContact(
          name: _accountContactNameCtrl.text.trim(),
          mobilePhone: _accountContactMobileCtrl.text.trim(),
          homePhone: _accountContactHomePhoneCtrl.text.trim(),
          addressLine1: _accountContactAddr1Ctrl.text.trim(),
          addressLine2: _accountContactAddr2Ctrl.text.trim(),
          addressLine3: _accountContactAddr3Ctrl.text.trim(),
          addressLine4: _accountContactAddr4Ctrl.text.trim(),
          postalCode: _accountContactPostalCodeCtrl.text.trim(),
          email: _accountContactEmailCtrl.text.trim(),
        ),
        results: ResultsInfo(
          matricYear: _matricYear,
          applicationLevel: _applicationLevel,
          upgrading: _upgrading,
          matricType: _matricType,
          examinationNumber: _examinationNumberCtrl.text.trim(),
          schoolLeavingCertificate: _schoolLeavingCertificate,
          subjects: _resultsSubjects,
        ),
        qualification: QualificationInfo(
          academicYear: _academicYear,
          choices: [
            QualificationChoice(
              faculty: _facultyCtrl.text.trim(),
              programme: _programmeCtrl.text.trim(),
            ),
          ],
          applicationPeriod: _applicationPeriod,
          studyMode: _studyMode,
          studyTiming: _studyTiming,
        ),
        agreement: AgreementInfo(
          loginPin: _loginPinCtrl.text.trim(),
          acceptanceStatus: _acceptanceStatus,
        ),
        uploadedDocuments: _uploadedFiles,
        grade12Subjects: _subjects,
        careerInterests: _careerInterests,
        onboardingComplete: existingProfile?.onboardingComplete ?? false,
      );

      await ref.read(profileProvider.notifier).saveProfile(profile);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Progress saved!'),
            duration: Duration(seconds: 1),
            backgroundColor: AppColors.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Save failed: $e'), backgroundColor: AppColors.error),
        );
      }
    }
    setState(() => _saving = false);
  }

  Widget _buildUploadDocumentsPage() {
    const labels = [
      'Final Grade 11 Report',
      'Term 1 Grade 12 Report',
      'Mid Year Grade 12 Report',
    ];
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Form(
        key: _formKeys[6],
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _SectionHeader(title: 'Upload Documents'),
            const SizedBox(height: 16),
            const Text(
              'Please upload the following supporting documents.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 20),
            ...List.generate(3, (i) {
              return Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLight,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(labels[i],
                        style: const TextStyle(
                            color: AppColors.primaryLight,
                            fontWeight: FontWeight.w600)),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () => _pickFile(i),
                        icon: Icon(
                          _uploadedFiles[i].isEmpty
                              ? Icons.cloud_upload_outlined
                              : Icons.check_circle_outline,
                          size: 18,
                          color: _uploadedFiles[i].isEmpty
                              ? AppColors.primaryLight
                              : AppColors.success,
                        ),
                        label: Text(
                          _uploadedFiles[i].isEmpty
                              ? 'Tap to upload'
                              : _uploadedFiles[i],
                          overflow: TextOverflow.ellipsis,
                        ),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: _uploadedFiles[i].isEmpty
                              ? AppColors.primaryLight
                              : AppColors.success,
                          side: BorderSide(
                            color: _uploadedFiles[i].isEmpty
                                ? AppColors.border
                                : AppColors.success,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Future<void> _pickFile(int index) async {
    final name = await pickFile('.pdf,.doc,.docx,.jpg,.jpeg,.png');
    if (name != null && mounted) {
      setState(() => _uploadedFiles[index] = name);
    }
  }

  Widget _buildBottomButtons() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          if (_currentPage > 0)
            Expanded(
              child: OutlinedButton(
                onPressed: () => _pageController.previousPage(
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeInOut,
                ),
                child: const Text('Back'),
              ),
            ),
          if (_currentPage > 0) const SizedBox(width: 8),
          Expanded(
            child: OutlinedButton(
              onPressed: _saving ? null : _saveCurrentPage,
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppColors.primary),
              ),
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: AppColors.primary),
                    )
                  : const Text('Save'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: ElevatedButton(
              onPressed: _saving ? null : _saveAndContinue,
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : Text(_currentPage < 6 ? 'Next' : 'Finish'),
            ),
          ),
        ],
      ),
    );
  }

}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Text(title,
        style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.bold));
  }
}
