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

    test('fixAction resolves empty-action POST forms against the page URL', () {
      final s = star.buildNavigationFixScript();
      expect(s, contains("var base = window.location.href;"));
      expect(s, contains("var before = form.getAttribute('action') || '';"));
    });

    test('submit is hijacked via a document capture listener + patched prototype', () {
      final s = star.buildNavigationFixScript();
      expect(s, contains("document.addEventListener('submit'"));
      expect(s, contains('HTMLFormElement.prototype.submit = submitWrapper;'));
      expect(s, contains('window.__ssaRealSubmit'));
    });
  });

  group('buildAutofillOnlyScript', () {
    test('uses the real oapIDnumber field id', () {
      final s = star.buildAutofillOnlyScript('{}');
      expect(s, contains("getElementById('oapIDnumber')"));
      expect(s, isNot(contains("getElementById('oapIdNumber')")));
    });

    test('injected selects get a name + matching _desc so wizard.js completes', () {
      final s = star.buildNavigationFixScript();
      expect(s, contains("select.name = 'custom-citz-code';"));
      expect(s, contains("citzDesc.id = 'custom-citz-code_desc';"));
      expect(s, contains("sel.name = 'ssa-heard-select';"));
      expect(s, contains("heardDesc.id = 'ssa-heard-select_desc';"));
    });

    test('doAutofill declares filled and applies the exact-name + fuzzy fill loops', () {
      final s = star.buildAutofillOnlyScript('{}');
      expect(s, contains('var filled = 0;'));
      expect(s, contains('for (var itsKey in itsExact)'));
      expect(s, contains('lowerIts[itsKey.toLowerCase()]'));
      expect(s, contains('var fk = fuzzyMatch(el2);'));
    });
  });
}