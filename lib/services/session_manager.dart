import 'dart:io';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';
import 'package:cookie_jar/cookie_jar.dart';
import 'package:flutter/foundation.dart';

/// Manages authenticated HTTP sessions for university portals.
/// Handles login, cookie persistence, and all subsequent requests.
class SessionManager {
  static const Duration _requestTimeout = Duration(seconds: 30);

  late final Dio _dio;
  late final CookieJar _cookieJar;

  bool _isLoggedIn = false;
  String? _baseUrl;
  String? _username;

  // ── Singleton ──────────────────────────────────────────────────────────────
  static final SessionManager _instance = SessionManager._internal();
  factory SessionManager() => _instance;

  SessionManager._internal() {
    _cookieJar = CookieJar();
    _dio = Dio(
      BaseOptions(
        connectTimeout: _requestTimeout,
        receiveTimeout: _requestTimeout,
        followRedirects: true,
        maxRedirects: 10,
        headers: {
          HttpHeaders.userAgentHeader:
              'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36',
          HttpHeaders.acceptHeader:
              'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'en-ZA,en;q=0.9',
        },
        validateStatus: (status) =>
            status != null && status >= 200 && status < 400,
      ),
    );

    _dio.interceptors.add(CookieManager(_cookieJar));

    // Debug logger (removed in release builds)
    if (kDebugMode) {
      _dio.interceptors.add(LogInterceptor(
        requestBody: false,
        responseBody: false,
        logPrint: (o) => debugPrint('[Session] $o'),
      ));
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  bool get isLoggedIn => _isLoggedIn;
  String? get baseUrl => _baseUrl;
  String? get username => _username;

  /// Logs into a university portal.
  ///
  /// [loginUrl]    — the POST URL for the login form (e.g. iEnabler login action)
  /// [credentials] — map of field-name → value matching the login form's inputs
  ///                 e.g. {'p_username': '12345678', 'p_password': 'secret'}
  /// [successIndicator] — a string that appears in the response HTML only when
  ///                      login succeeds (e.g. 'Welcome' or 'My Applications')
  Future<SessionResult> login({
    required String loginUrl,
    required Map<String, String> credentials,
    String successIndicator = 'Welcome',
  }) async {
    try {
      _isLoggedIn = false;
      _baseUrl = Uri.parse(loginUrl).origin;
      _username = credentials['p_username'] ?? credentials['username'];

      // Step 1: GET the login page first — picks up any pre-session cookies
      await _dio.get(loginUrl);

      // Step 2: POST the credentials
      final response = await _dio.post(
        loginUrl,
        data: FormData.fromMap(credentials),
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
          headers: {
            HttpHeaders.refererHeader: loginUrl,
          },
        ),
      );

      final body = response.data?.toString() ?? '';

      if (body.contains(successIndicator)) {
        _isLoggedIn = true;
        debugPrint('[Session] Login successful for $_username');
        return SessionResult.success(responseBody: body);
      } else if (_isErrorBody(body)) {
        return SessionResult.failure(
            message: _extractError(body) ?? 'Login failed — check credentials');
      } else {
        // Some portals redirect without a keyword — treat non-error as success
        _isLoggedIn = true;
        return SessionResult.success(responseBody: body);
      }
    } on DioException catch (e) {
      return SessionResult.failure(message: _dioError(e));
    } catch (e) {
      return SessionResult.failure(message: e.toString());
    }
  }

  /// Fetches a page (GET) using the current authenticated session.
  /// Returns the raw HTML body.
  Future<SessionResult> getPage(String url) async {
    _assertLoggedIn();
    try {
      final response = await _dio.get(
        url,
        options: Options(headers: {HttpHeaders.refererHeader: _baseUrl}),
      );
      return SessionResult.success(responseBody: response.data?.toString());
    } on DioException catch (e) {
      return SessionResult.failure(message: _dioError(e));
    }
  }

  /// Submits a form via HTTP POST.
  ///
  /// [actionUrl] — the form's `action` attribute URL
  /// [fields]    — all field name→value pairs (including hidden fields)
  /// [referer]   — the page the form was on (used as Referer header)
  Future<SessionResult> postForm({
    required String actionUrl,
    required Map<String, String> fields,
    String? referer,
  }) async {
    _assertLoggedIn();
    try {
      // Build URL-encoded body manually to preserve field order (important for
      // Oracle APEX p_arg_names / p_arg_values paired arrays).
      final encoded = _encodeFields(fields);

      final response = await _dio.post(
        actionUrl,
        data: encoded,
        options: Options(
          contentType: Headers.formUrlEncodedContentType,
          headers: {
            HttpHeaders.refererHeader: referer ?? _baseUrl,
          },
        ),
      );

      return SessionResult.success(
        responseBody: response.data?.toString(),
        finalUrl: response.realUri.toString(),
      );
    } on DioException catch (e) {
      return SessionResult.failure(message: _dioError(e));
    }
  }

  /// Logs out and clears all cookies.
  Future<void> logout() async {
    try {
      if (_baseUrl != null) {
        await _dio.get('$_baseUrl/apex/f?p=PRODI41:LOGOUT');
      }
    } catch (_) {
      // Best-effort logout
    } finally {
      await _cookieJar.deleteAll();
      _isLoggedIn = false;
      _username = null;
      debugPrint('[Session] Logged out, cookies cleared');
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  void _assertLoggedIn() {
    if (!_isLoggedIn) {
      throw StateError(
          'SessionManager: not logged in. Call login() first.');
    }
  }

  /// URL-encodes fields preserving insertion order.
  String _encodeFields(Map<String, String> fields) {
    return fields.entries
        .map((e) =>
            '${Uri.encodeQueryComponent(e.key)}=${Uri.encodeQueryComponent(e.value)}')
        .join('&');
  }

  bool _isErrorBody(String body) {
    final lower = body.toLowerCase();
    return lower.contains('invalid') ||
        lower.contains('incorrect') ||
        lower.contains('error') ||
        lower.contains('failed');
  }

  String? _extractError(String body) {
    // Simple regex to pull error message from common portal patterns
    final match =
        RegExp(r'<[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</', caseSensitive: false)
            .firstMatch(body);
    if (match != null) {
      return match.group(1)
          ?.replaceAll(RegExp(r'<[^>]+>'), '')
          .trim();
    }
    return null;
  }

  String _dioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Connection timed out — check your internet connection';
      case DioExceptionType.badResponse:
        return 'Server returned ${e.response?.statusCode} — try again later';
      case DioExceptionType.connectionError:
        return 'Cannot reach the university portal — check internet or VPN';
      default:
        return e.message ?? e.toString();
    }
  }
}

// ── Result type ────────────────────────────────────────────────────────────────

class SessionResult {
  final bool success;
  final String? responseBody;
  final String? finalUrl;
  final String? errorMessage;

  const SessionResult._({
    required this.success,
    this.responseBody,
    this.finalUrl,
    this.errorMessage,
  });

  factory SessionResult.success({String? responseBody, String? finalUrl}) =>
      SessionResult._(
          success: true, responseBody: responseBody, finalUrl: finalUrl);

  factory SessionResult.failure({required String message}) =>
      SessionResult._(success: false, errorMessage: message);

  @override
  String toString() => success
      ? 'SessionResult.success(url: $finalUrl)'
      : 'SessionResult.failure($errorMessage)';
}
