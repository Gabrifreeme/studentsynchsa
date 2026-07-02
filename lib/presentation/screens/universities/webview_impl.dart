import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/repositories/profile_repository_impl.dart';
import 'package:studentsyncsa/domain/models/student_profile.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;
import 'package:studentsyncsa/services/profile_validator.dart';

class AppWebView extends StatefulWidget {
  final String url;
  final String universityName;
  final StudentProfile? profile;
  const AppWebView({
    super.key,
    required this.url,
    required this.universityName,
    this.profile,
  });

  @override
  State<AppWebView> createState() => _AppWebViewState();
}

enum AutofillStatus { idle, running, done, error }

class _AppWebViewState extends State<AppWebView> {
  late final WebViewController _controller;
  bool _loading = true;
  StudentProfile? _profile;
  AutofillStatus _autofillStatus = AutofillStatus.idle;
  final Set<String> _filledFields = {};

  // ── Sections — mapKeys match StudentProfile.toJson() exactly ─────────────
  // Dot-notation: 'personal.lastName' → toJson()['personal']['lastName']
  // Fields with no model backing are omitted (passportNo, nokRelation,
  // nokInitials, studyPermit) — they would always show '—'.
  static const _sections = [
    _Section('Personal', [
      ('oapSurname',     'personal.lastName',         false),
      ('oapInitials',    'personal.initials',         false),
      ('oapIdNumber',    'personal.idNumber',         false),
      ('oapDateOfBirth', 'personal.dateOfBirth',      false),
      ('oapGender',      'personal.gender',           true),
    ]),
    _Section('Contact', [
      ('oapEmail',        'contact.email',            false),
      ('oapEmailConfirm', 'contact.email',            false),
      ('oapCellNo',       'contact.phone',            false),
      ('oapTelNo',        'contact.workPhone',        false),
    ]),
    _Section('Address', [
      ('oapStreet',     'address.address',            false),
      ('oapSuburb',     'address.addressLine2',       false),
      ('oapCity',       'address.addressLine3',       false),
      ('oapPostalCode', 'address.postalCode',         false),
    ]),
    _Section('Postal Address', [
      ('oapPostStreet', 'address.postalAddress',      false),
      ('oapPostCode',   'address.postalCode',         false),
    ]),
    _Section('Next of Kin', [
      ('oapNokNames',   'nextOfKin.name',             false),
      ('oapNokCell',    'nextOfKin.mobilePhone',      false),
      ('oapNokEmail',   'nextOfKin.email',            false),
    ]),
    _Section('School', [
      ('oapSchoolName', 'school.schoolName',          false),
      ('oapSchoolYear', 'school.yearOfMatric',        false),
    ]),
    _Section('Citizenship', [
      ('oapCitizenType', 'demographic.nationality',   true),
    ]),
  ];

  @override
  void initState() {
    super.initState();
    _profile = widget.profile;
    _loadProfileIfMissing();
    // Hard reset: clear cookies + cache for a fresh session
    WebViewCookieManager().clearCookies();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setUserAgent(
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
      ..setNavigationDelegate(NavigationDelegate(
        onNavigationRequest: (request) {
          final url = request.url.toString();
          debugPrint("Navigating to: $url");
          if (url.contains("pls/prodi")) {
            final uri = Uri.parse(url);
            launchUrl(uri, mode: LaunchMode.externalApplication);
            return NavigationDecision.prevent;
          }
          return NavigationDecision.navigate;
        },
        onWebResourceError: (error) {
          debugPrint("PAGE LOAD ERROR: ${error.description} (code: ${error.errorCode})");
          if (error.errorCode == -105 || error.description.contains("ERR_NAME_NOT_RESOLVED")) {
            showDialog(
              context: context,
              builder: (ctx) => AlertDialog(
                title: const Text("Portal Offline"),
                content: const Text("The university portal is currently unreachable. Please try again later or open in your browser."),
                actions: [
                  TextButton(
                    onPressed: () => launchUrl(Uri.parse("https://www.univen.ac.za/"), mode: LaunchMode.externalApplication),
                    child: const Text("Open in Browser"),
                  ),
                ],
              ),
            );
          }
        },
        onProgress: (progress) {
          if (progress == 100) {
            debugPrint("Page loaded successfully");
          }
        },
        onPageStarted: (_) {
          _controller.clearCache();
          setState(() {
            _loading = true;
            _filledFields.clear();
            _autofillStatus = AutofillStatus.idle;
          });
        },
        onPageFinished: (url) async {
          setState(() => _loading = false);

          // ── Force desktop scaling + click Apply Online ──
          await _controller.runJavaScript('''
var meta = document.createElement('meta');
meta.name = 'viewport';
meta.content = 'width=1200, initial-scale=0.5';
document.getElementsByTagName('head')[0].appendChild(meta);
var links = document.querySelectorAll('a');
for (var i = 0; i < links.length; i++) {
  if (links[i].innerText.includes('Apply Online')) {
    links[i].click();
  }
}
''');

          await _runPortalPatches();

          // ── Navigate to ITS application portal ──
          await _controller.runJavaScript('''
var link = document.querySelector('a[href*="gen.gw1pkg"]');
if (link) {
  window.location.href = link.href;
  console.log("Navigating to: " + link.href);
} else {
  console.log("Could not find the application link!");
}
''');

          // ── Auto-fill injection with 500ms DOM readiness delay ──
          await Future.delayed(const Duration(milliseconds: 500));
          if (_profile != null) {
            final profileJson = jsonEncode(_profile!.toJson());
            final script = star.buildAutofillScript(profileJson);
            await _controller.runJavaScript(script);
            debugPrint("Autofill script injected successfully into: $url");
          }
        },
      ))
      ..loadRequest(Uri.parse(widget.url));
  }

  Future<void> _loadProfileIfMissing() async {
    if (_profile != null) return;
    final repo = ProfileRepositoryImpl();
    var p = await repo.getProfile();
    if (p == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      p = await repo.getProfile();
    }
    if (p == null) {
      await Future.delayed(const Duration(milliseconds: 500));
      p = await repo.getProfile();
    }
    if (p != null && mounted) setState(() => _profile = p);
  }

  // toJson() is the correct method — StudentProfile has no toMap()
  Map<String, dynamic> get _data => _profile?.toJson() ?? {};

  // ── Dot-notation resolver ─────────────────────────────────────────────────
  // Walks 'personal.lastName' → _data['personal']['lastName']
  String _resolveValue(String dotPath) {
    final parts = dotPath.split('.');
    dynamic node = _data;
    for (final part in parts) {
      if (node is! Map) return '';
      node = node[part];
      if (node == null) return '';
    }
    // int/bool → string, null → ''
    if (node is String) return node;
    if (node is int || node is double || node is bool) return node.toString();
    return '';
  }

  // ── Normalisation ─────────────────────────────────────────────────────────

  String _normalize(String oapName, String rawValue) {
    if (rawValue.isEmpty) return '';
    switch (oapName) {
      case 'oapDateOfBirth':
        return _dateToOracle(rawValue);
      case 'oapCellNo':
      case 'oapTelNo':
      case 'oapNokCell':
        return _saPhone(rawValue) ?? rawValue;
      case 'oapGender':
        final g = rawValue.toUpperCase();
        if (g == 'FEMALE' || g == 'F') return 'F';
        if (g == 'MALE'   || g == 'M') return 'M';
        return rawValue;
      case 'oapCitizenType':
        final n = rawValue.toLowerCase();
        if (n.contains('south african') || n == 'sa' || n == 'rsa') return 'Y';
        if (n == 'true'  || n == 'yes' || n == 'y') return 'Y';
        if (n == 'false' || n == 'no'  || n == 'n') return 'N';
        return rawValue;
      default:
        return rawValue;
    }
  }

  String _dateToOracle(String raw) {
    // ISO: 2005-03-21T00:00:00.000 or 2005-03-21
    final iso = RegExp(r'^(\d{4})-(\d{2})-(\d{2})').firstMatch(raw);
    if (iso != null) return '${iso[3]}/${iso[2]}/${iso[1]}';
    // Already DD/MM/YYYY
    final dmy4 = RegExp(r'^(\d{2})[/\-](\d{2})[/\-](\d{4})$').firstMatch(raw);
    if (dmy4 != null) return '${dmy4[1]}/${dmy4[2]}/${dmy4[3]}';
    return '';
  }

  String? _saPhone(String raw) {
    final d = raw.replaceAll(RegExp(r'\D'), '');
    if (d.length == 11 && d.startsWith('27')) return '0${d.substring(2)}';
    if (d.length == 10 && d.startsWith('0'))  return d;
    if (d.length == 9)                         return '0$d';
    return null;
  }

  // ── Per-field inject (red tick) ───────────────────────────────────────────

  Future<void> _injectField(String oapName, String rawValue) async {
    final normalized = _normalize(oapName, rawValue);
    if (normalized.isEmpty) return;
    final result = await _controller.runJavaScriptReturningResult(
        star.buildInjectScript(oapName, normalized));
    final success = result.toString().trim() == 'true';
    if (mounted && success) {
      setState(() => _filledFields.add(oapName));
      await Future.delayed(const Duration(seconds: 2));
      if (mounted) setState(() => _filledFields.remove(oapName));
    }
  }

  // ── Fill All ──────────────────────────────────────────────────────────────

  Future<void> _runAutofill() async {
    if (_profile == null) {
      _snack('No profile loaded yet.', isError: true);
      return;
    }

    final missing = ProfileValidator.missingFields(_profile!);
    if (missing.isNotEmpty) {
      _snack(
        'Complete your profile first: ${missing.take(3).join(', ')}'
        '${missing.length > 3 ? ' (+${missing.length - 3} more)' : ''}',
        isError: true,
      );
      return;
    }

    if (!mounted) return;
    setState(() => _autofillStatus = AutofillStatus.running);

    // Pass JSON string — buildCompleteAutofillScript includes retry passes
    await _controller.runJavaScript(
        star.buildCompleteAutofillScript(jsonEncode(_profile!.toJson())));

    if (!mounted) return;
    setState(() => _autofillStatus = AutofillStatus.done);

    // The JS toast inside the WebView shows the exact field count.
    // We just show a brief Flutter snackbar to confirm the script fired.
    _snack('✅ Autofill sent — check the form above');

    await Future.delayed(const Duration(seconds: 4));
    if (mounted) setState(() => _autofillStatus = AutofillStatus.idle);
  }

  void _snack(String msg, {bool isError = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: isError ? const Color(0xFFEF4444) : const Color(0xFF10B981),
      behavior: SnackBarBehavior.floating,
      duration: Duration(seconds: isError ? 5 : 3),
    ));
  }

  // ── Long-press debug: list all named fields on the current page ───────────

  Future<void> _showFieldDebug() async {
    final raw = await _controller.runJavaScriptReturningResult(
        star.buildFieldScanScript());
    if (!mounted) return;
    final lines = raw.toString()
        .split('\n')
        .where((l) => l.trim().isNotEmpty)
        .toList();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Fields on this page',
            style: TextStyle(color: Colors.white)),
        backgroundColor: const Color(0xFF0F1624),
        content: SizedBox(
          width: double.maxFinite,
          child: lines.isEmpty
              ? const Text('No named fields found.',
                  style: TextStyle(color: Colors.white70))
              : ListView.builder(
                  shrinkWrap: true,
                  itemCount: lines.length,
                  itemBuilder: (_, i) {
                    final parts = lines[i].split('|');
                    final name = parts.isNotEmpty ? parts[0] : '';
                    final type = parts.length > 1 ? parts[1] : '';
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Text(
                        '$type[name="$name"]',
                        style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 11,
                            fontFamily: 'monospace'),
                      ),
                    );
                  },
                ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Close')),
        ],
      ),
    );
  }

  // ── Portal patches ────────────────────────────────────────────────────────

  Future<void> _runPortalPatches() async {
    try {
      await _controller.runJavaScript(star.buildBlanketAutofillSuppressScript());
      await _controller.runJavaScript(star.buildSecurityPatch());
      await _controller.runJavaScript(star.buildLabelPatch());
      await _controller.runJavaScript(star.buildAutocompletePatch());
      await _controller.runJavaScript(star.buildSelectAutocompletePatch());
      await _controller.runJavaScript(star.buildProvinceDisambiguationPatch());
      await _controller.runJavaScript(star.buildFocusPatch());
      await _controller.runJavaScript(star.buildInputmodePatch());
      await _controller.runJavaScript(star.buildFormLabelPatch());
    } catch (_) {}
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.universityName),
        backgroundColor: AppColors.surface,
      ),
      body: Column(
        children: [
          // Top pane — university form
          Expanded(
            child: Stack(
              children: [
                WebViewWidget(controller: _controller),
                if (_loading)
                  const Center(child: CircularProgressIndicator()),
              ],
            ),
          ),
          // Bottom pane — My Profile
          _buildPanel(),
        ],
      ),
    );
  }

  // ── My Profile panel ──────────────────────────────────────────────────────

  Widget _buildPanel() {
    return Container(
      height: 260,
      decoration: BoxDecoration(
        color: const Color(0xFF0F1624),
        border: const Border(
            top: BorderSide(color: Color(0xFF7C3AED), width: 1)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF7C3AED).withValues(alpha: 0.15),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        children: [
          // Header
          Padding(
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                const Text('📋', style: TextStyle(fontSize: 16)),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text(
                    'My Profile',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w600),
                  ),
                ),
                _buildStatusChip(),
                const SizedBox(width: 8),
                // Fill All — long-press opens field debug scanner
                GestureDetector(
                  onLongPress: _showFieldDebug,
                  child: SizedBox(
                    height: 32,
                    child: ElevatedButton.icon(
                      onPressed: _autofillStatus == AutofillStatus.running
                          ? null
                          : _runAutofill,
                      icon: _autofillStatus == AutofillStatus.running
                          ? const SizedBox(
                              width: 14,
                              height: 14,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.auto_awesome, size: 16),
                      label: const Text('Fill All',
                          style: TextStyle(fontSize: 12)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF7C3AED),
                        foregroundColor: Colors.white,
                        padding:
                            const EdgeInsets.symmetric(horizontal: 12),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: Color(0xFF2A2A3A)),
          // Field list
          Expanded(
            child: ListView(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              children: [
                for (final sec in _sections) ...[
                  _buildSectionHeader(sec.label),
                  const SizedBox(height: 2),
                  for (final f in sec.fields) ...[
                    _buildFieldRow(f.$1, f.$2),
                    const SizedBox(height: 1),
                  ],
                  const SizedBox(height: 4),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusChip() {
    switch (_autofillStatus) {
      case AutofillStatus.done:
        return _chip('Sent ✓', Colors.green);
      case AutofillStatus.running:
        return _chip('Filling…', Colors.amber);
      case AutofillStatus.error:
        return _chip('Error', Colors.red);
      case AutofillStatus.idle:
        return const SizedBox.shrink();
    }
  }

  Widget _chip(String label, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.2),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(label,
            style: TextStyle(color: color, fontSize: 11)),
      );

  Widget _buildSectionHeader(String label) => Padding(
        padding: const EdgeInsets.only(top: 6, bottom: 1),
        child: Text(
          label.toUpperCase(),
          style: const TextStyle(
            color: Color(0xFF7C3AED),
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.8,
          ),
        ),
      );

  // Each row: label | value | red-tick inject button
  Widget _buildFieldRow(String oapName, String dotPath) {
    final raw     = _resolveValue(dotPath);
    final display = raw.isNotEmpty ? _displayValue(oapName, raw) : '—';
    final hasValue = raw.isNotEmpty;
    final filled  = _filledFields.contains(oapName);

    return GestureDetector(
      onTap: hasValue ? () => _injectField(oapName, raw) : null,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 5),
        decoration: BoxDecoration(
          color: filled
              ? Colors.green.withValues(alpha: 0.08)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(4),
        ),
        child: Row(
          children: [
            // Field label
            SizedBox(
              width: 76,
              child: Text(
                _fieldLabel(oapName),
                style: const TextStyle(
                    color: Color(0xFF888899), fontSize: 11),
              ),
            ),
            // Value
            Expanded(
              child: Text(
                display,
                style: TextStyle(
                  color: filled
                      ? Colors.green
                      : hasValue
                          ? Colors.white
                          : const Color(0xFF555566),
                  fontSize: 12,
                  fontWeight:
                      hasValue ? FontWeight.w500 : FontWeight.w300,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            // Red tick — tapping injects this field only
            if (hasValue)
              Padding(
                padding: const EdgeInsets.only(left: 4),
                child: Icon(
                  filled
                      ? Icons.check_circle        // green: just injected
                      : Icons.check_circle_outline,// red: tap to inject
                  size: 16,
                  color: filled
                      ? Colors.green
                      : const Color(0xFFEF4444),
                ),
              ),
          ],
        ),
      ),
    );
  }

  // Human-readable display for certain normalised fields
  String _displayValue(String oapName, String raw) {
    switch (oapName) {
      case 'oapDateOfBirth':
        final oracle = _dateToOracle(raw);
        return oracle.isNotEmpty ? oracle : raw;
      case 'oapCitizenType':
        final n = raw.toLowerCase();
        if (n.contains('south african') || n == 'sa' || n == 'rsa') {
          return 'SA Citizen (Y)';
        }
        return raw;
      default:
        return raw;
    }
  }

  String _fieldLabel(String oapName) => switch (oapName) {
    'oapSurname'      => 'Surname',
    'oapInitials'     => 'Initials',
    'oapIdNumber'     => 'ID No',
    'oapDateOfBirth'  => 'DOB',
    'oapGender'       => 'Gender',
    'oapEmail'        => 'Email',
    'oapEmailConfirm' => 'Email (×2)',
    'oapCellNo'       => 'Cell',
    'oapTelNo'        => 'Tel',
    'oapStreet'       => 'Street',
    'oapSuburb'       => 'Suburb',
    'oapCity'         => 'City',
    'oapPostalCode'   => 'Post Code',
    'oapPostStreet'   => 'Post Addr',
    'oapPostCode'     => 'Post Code',
    'oapNokNames'     => 'NOK Name',
    'oapNokCell'      => 'NOK Cell',
    'oapNokEmail'     => 'NOK Email',
    'oapSchoolName'   => 'School',
    'oapSchoolYear'   => 'Matric Yr',
    'oapCitizenType'  => 'Citizen',
    _                 => oapName,
  };
}

class _Section {
  final String label;
  final List<(String, String, bool)> fields;
  const _Section(this.label, this.fields);
}
