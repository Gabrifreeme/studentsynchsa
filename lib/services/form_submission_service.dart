import 'session_manager.dart';
import 'html_form_parser.dart';
import 'package:flutter/foundation.dart';

/// Orchestrates a full portal interaction: login → scrape form → merge
/// profile → POST submission — without any WebView manipulation.
///
/// The flow:
///  1. [login] — GETs the portal to establish a session, then POSTs credentials
///               (defaults to ITS iEnabler's P_STUDENT_NO / P_PIN fields)
///  2. [submitApplicationForm] — GETs the application page, parses the HTML
///     form, merges the user's profile into the visible fields (keeping hidden
///     tokens intact), and POSTs the result to the server.
///
/// Example:
/// ```dart
/// final service = FormSubmissionService(
///   applicationUrl: 'https://univenierp01.univen.ac.za/pls/prodi41/...',
/// );
///
/// await service.login(studentNumber: '12345678', password: 'secret');
///
/// final result = await service.submitApplicationForm(
///   studentProfile: { 'P_SURNAME': 'Doe', 'P_FIRST_NAMES': 'John', ... },
/// );
///
/// if (result.success && result.responseBody != null) {
///   webViewController.loadHtmlString(result.responseBody!);
/// }
/// ```
class FormSubmissionService {
  final SessionManager _session;
  final String _applicationUrl;

  FormSubmissionService({
    this._applicationUrl =
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
  }) : _session = SessionManager();

  // ── Public API ─────────────────────────────────────────────────────────────

  /// Logs into the university portal.
  ///
  /// Internally this:
  ///   1. GETs the portal to pick up session cookies
  ///   2. POSTs [studentNumber]/[password] as P_STUDENT_NO / P_PIN
  ///
  /// [loginUrl] overrides the target POST URL (defaults to [applicationUrl]).
  /// [extraCredentials] allows adding more hidden/required fields.
  /// [successIndicator] the string in the response HTML that signals success
  ///                     (default: empty string — non-error = success).
  Future<FormSubmissionResult> login({
    required String studentNumber,
    required String password,
    String? loginUrl,
    Map<String, String>? extraCredentials,
    String successIndicator = '',
  }) async {
    final postUrl = loginUrl ?? _applicationUrl;

    final credentials = <String, String>{
      'P_STUDENT_NO': studentNumber,
      'P_PIN': password,
      ...?extraCredentials,
    };

    debugPrint('[FormSubmission] Logging in as $studentNumber → $postUrl');

    final result = await _session.login(
      loginUrl: postUrl,
      credentials: credentials,
      successIndicator: successIndicator,
    );

    return FormSubmissionResult._fromSessionResult(result);
  }

  /// Fetches the application form, merges [studentProfile] values, and POSTs.
  ///
  /// [formPageUrl] — the URL of the application form page (defaults to the
  ///                 service's [applicationUrl]).
  /// [studentProfile] — a map of form field name → value from the user's
  ///                    profile (e.g. `{'P_SURNAME': 'Doe'}`). Only fields
  ///                    that match the parsed form's field names are merged.
  Future<FormSubmissionResult> submitApplicationForm({
    required Map<String, String> studentProfile,
    String? formPageUrl,
  }) async {
    final pageUrl = formPageUrl ?? _applicationUrl;

    // 1. GET the form page
    debugPrint('[FormSubmission] Fetching form page → $pageUrl');
    final pageResult = await _session.getPage(pageUrl);
    if (!pageResult.success || pageResult.responseBody == null) {
      return FormSubmissionResult(
        success: false,
        errorMessage:
            pageResult.errorMessage ?? 'Failed to load application form page',
      );
    }

    // 2. Parse the form from HTML
    final form = parsePortalForm(pageResult.responseBody!);
    if (form.action.isEmpty) {
      return FormSubmissionResult(
        success: false,
        errorMessage: 'No form found on the application page',
      );
    }
    if (form.fields.isEmpty) {
      return FormSubmissionResult(
        success: false,
        errorMessage: 'Form has no fields — the page may be JS-rendered',
      );
    }

    debugPrint('[FormSubmission] Found ${form.fields.length} fields '
        '(${form.fillableFields.length} fillable, '
        '${form.hiddenFields.length} hidden)');

    // 3. Merge student profile into the field map
    final fieldMap = form.mergeValues(studentProfile);
    debugPrint('[FormSubmission] POSTing ${fieldMap.length} fields');

    // 4. Submit the form
    final postResult = await _session.postForm(
      actionUrl: form.action,
      fields: fieldMap,
      referer: pageUrl,
    );

    return FormSubmissionResult._fromSessionResult(postResult);
  }

  // ── Convenience ────────────────────────────────────────────────────────────

  /// True after a successful [login] call.
  bool get isLoggedIn => _session.isLoggedIn;

  /// The base URL extracted from the login URL.
  String? get baseUrl => _session.baseUrl;

  /// Logs out and clears session cookies.
  Future<void> logout() => _session.logout();
}

// ── Result type ────────────────────────────────────────────────────────────────

/// The result of a login or form-submission operation.
class FormSubmissionResult {
  final bool success;
  final String? responseBody;
  final String? finalUrl;
  final String? errorMessage;

  const FormSubmissionResult({
    required this.success,
    this.responseBody,
    this.finalUrl,
    this.errorMessage,
  });

  factory FormSubmissionResult._fromSessionResult(SessionResult r) =>
      FormSubmissionResult(
        success: r.success,
        responseBody: r.responseBody,
        finalUrl: r.finalUrl,
        errorMessage: r.errorMessage,
      );

  /// Alias for [responseBody] — the raw HTML returned after form submission.
  String? get resultHtml => responseBody;

  @override
  String toString() => success
      ? 'FormSubmissionResult.success(url: $finalUrl)'
      : 'FormSubmissionResult.failure($errorMessage)';
}
