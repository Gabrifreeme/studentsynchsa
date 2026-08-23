import 'package:flutter_test/flutter_test.dart';
import 'package:studentsyncsa/services/autofill_script.dart' as star;

void main() {
  group('buildNavigationFixScript', () {
    test('contains the aggressive-truncation and view->proc helpers', () {
      final s = star.buildNavigationFixScript();
      for (final needle in <String>[
        '_expandFromMarker',
        'rewriteViewToProc',
        'submitViaFetch',
        'isItsPostForm',
      ]) {
        expect(s, contains(needle), reason: 'missing: $needle');
      }
    });

    test('rewriteViewToProc maps gw1view to gw1proc for POST forms', () {
      final s = star.buildNavigationFixScript();
      expect(s, contains('(gen.gw1pkg.gw1)view'));
      expect(s, contains("method === 'POST'"));
    });

    test('submitViaFetch handles redirects natively and avoids white pages', () {
      final s = star.buildNavigationFixScript();
      expect(s, contains("redirect: 'manual'"));
      expect(s, contains('opaqueredirect'));
      expect(s, contains("res.headers.get('Location')"));
      expect(s, contains('blank POST response, navigating natively'));
      expect(s, contains('window.__ssaRealSubmit'));
    });

    test('fixAction falls back to the page URL for empty-action POST forms', () {
      final s = star.buildNavigationFixScript();
      expect(s, contains("var base = before || form.action || window.location.href;"));
    });

    test('submit listener lives on window; unnamed selects get _desc guards', () {
      final s = star.buildNavigationFixScript();
      expect(s, contains("window.addEventListener('submit'"));
      expect(s, contains('ssaFixUnnamedSelects'));
      expect(s, contains("el.name ? el.name + '_desc' : '_desc'"));
    });
  });

  group('buildAutofillOnlyScript', () {
    test('uses the real oapIDnumber field id', () {
      final s = star.buildAutofillOnlyScript('{}');
      expect(s, contains("getElementById('oapIDnumber')"));
      expect(s, isNot(contains("getElementById('oapIdNumber')")));
    });
  });
}