import 'package:flutter_test/flutter_test.dart';
import 'package:studentsyncsa/services/its_url_fixer.dart';

void main() {
  group('ItsUrl.expandProcedure', () {
    test('expands gw1v -> gw1view and preserves query string', () {
      expect(
        ItsUrl.expandProcedure(
          'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1v?p_calling_proc=gw1view',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?p_calling_proc=gw1view',
      );
    });

    test('expands gw1p -> gw1proc and preserves query string', () {
      expect(
        ItsUrl.expandProcedure(
          'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1p?x_form_proc=gw1proc',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1proc?x_form_proc=gw1proc',
      );
    });

    test('expands truncated URL with a fragment', () {
      expect(
        ItsUrl.expandProcedure('https://h/pls/prodi41/gen.gw1pkg.gw1v#sec'),
        'https://h/pls/prodi41/gen.gw1pkg.gw1view#sec',
      );
    });

    test('leaves already-whole names untouched', () {
      expect(
        ItsUrl.expandProcedure(
          'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?x=1',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?x=1',
      );
      expect(
        ItsUrl.expandProcedure(
          'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1proc',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1proc',
      );
      expect(
        ItsUrl.expandProcedure(
          'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP',
      );
    });

    test('leaves non-procedure ITS URLs untouched (w99pkg student portal)', () {
      const login = 'https://univenierp01.univen.ac.za/pls/prodi41/w99pkg.mi_login';
      expect(ItsUrl.expandProcedure(login), login);
    });

    test('works on relative URLs (the form the page itself uses)', () {
      expect(ItsUrl.expandProcedure('gen.gw1pkg.gw1v?p_calling_proc=x'),
          'gen.gw1pkg.gw1view?p_calling_proc=x');
    });
  });

  group('ItsUrl.normalize', () {
    test('fixes host typo unlven -> univen', () {
      expect(
        ItsUrl.normalize(
          'https://unlvenierp01.unlven.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
      );
    });

    test('fixes host typo univenerp01 -> univenierp01', () {
      expect(
        ItsUrl.normalize(
          'https://univenerp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
      );
    });

    test('upgrades plain http to https for ITS URLs', () {
      expect(
        ItsUrl.normalize(
          'http://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
      );
    });

    test('combines truncation + typo + http in one pass', () {
      expect(
        ItsUrl.normalize(
          'http://unlvenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1v?p=1',
        ),
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?p=1',
      );
    });

    test('is idempotent', () {
      const cases = [
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1v?p_calling_proc=gw1view',
        'http://unlvenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1p?x=1',
        'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view',
        'https://univenierp01.univen.ac.za/pls/prodi41/w99pkg.mi_login',
      ];
      for (final c in cases) {
        final once = ItsUrl.normalize(c);
        expect(ItsUrl.normalize(once), once, reason: 'not idempotent: $c');
      }
    });

    test('leaves non-ITS URLs untouched', () {
      const nonIts = [
        'https://www.univen.ac.za/apply',
        'https://www.univen.ac.za',
        'https://www.ufs.ac.za/apply',
        'https://www.google.com/search?q=univen',
      ];
      for (final c in nonIts) {
        expect(ItsUrl.normalize(c), c, reason: 'should be untouched: $c');
      }
    });

    test('leaves other universities ITS portals untouched (CPUT alecto)', () {
      const cput =
          'https://alecto.cput.ac.za/pls/prodi41/w99pkg.mi_login';
      expect(ItsUrl.normalize(cput), cput);
    });

    test('empty string stays empty', () {
      expect(ItsUrl.normalize(''), '');
    });
  });

  group('ItsUrl.isItsHost / hasProcedure', () {
    test('detects ITS hosts', () {
      expect(ItsUrl.isItsHost('https://univenierp01.univen.ac.za/pls/prodi41/x'), isTrue);
      expect(ItsUrl.isItsHost('http://unlvenierp01.univen.ac.za/pls/x'), isTrue);
      expect(ItsUrl.isItsHost('https://alecto.cput.ac.za/pls/prodi41/w99pkg.mi_login'), isTrue);
      expect(ItsUrl.isItsHost('https://www.univen.ac.za'), isFalse);
      expect(ItsUrl.isItsHost('https://www.google.com'), isFalse);
    });

    test('detects procedure markers', () {
      expect(ItsUrl.hasProcedure('gen.gw1pkg.gw1v?x=1'), isTrue);
      expect(ItsUrl.hasProcedure('.../gen.gw1pkg.gw1proc'), isTrue);
      expect(ItsUrl.hasProcedure('w99pkg.mi_login'), isFalse);
      expect(ItsUrl.hasProcedure('https://www.univen.ac.za'), isFalse);
    });
  });
}
