/// Normalization for Oracle ITS (PL/SQL) portal URLs — used by the Venda
/// (UNIVEN) online application wizard, which lives on
/// `https://univenierp01.univen.ac.za/pls/prodi41/` and builds navigations
/// with procedure names like `gen.gw1pkg.gw1view` (GET pages) and
/// `gen.gw1pkg.gw1proc` (POST handlers).
///
/// Under some conditions the procedure name arrives truncated
/// (`gen.gw1pkg.gw1v` / `gen.gw1pkg.gw1p`) and the server answers 404
/// ("The requested URL ... was not found."). These helpers restore the full
/// procedure name, repair the `unlven`/`univenerp01` host typos the portal
/// occasionally emits, and upgrade plain http to https. They are idempotent
/// and preserve the query string.
library;

class ItsUrl {
  const ItsUrl._();

  /// Full ITS procedure-name prefix, e.g. `gen.gw1pkg.gw1view`.
  static const String procedureMarker = 'gen.gw1pkg.gw1';

  /// True when [url] points at an ITS portal host or path.
  static bool isItsHost(String url) {
    return url.contains('univenierp01') ||
        url.contains('univenerp01') ||
        url.contains('univenerip01') ||
        url.contains('unlvenierp01') ||
        url.contains('/pls/prodi41') ||
        url.contains('/pls/');
  }

  /// True when [url] carries a `gen.gw1pkg.gw1...` procedure name.
  static bool hasProcedure(String url) => url.contains(procedureMarker);

  /// Expand a truncated ITS procedure name. Known truncations:
  /// `gw1v` -> `gw1view`, `gw1p` -> `gw1proc`.
  /// Aggressive truncations from 64-char URL limits:
  /// `gwa`/`gwas`/`gwav`/`gwavs` -> `gw1view`
  /// `gw1p`/`gw1pr`/`gw1pro` -> `gw1proc`
  /// Idempotent — returns [url] unchanged when there is nothing to fix
  /// or the name is already whole.
  static String expandProcedure(String url) {
    final i = url.indexOf(procedureMarker);
    if (i == -1) return url;
    final restStart = i + procedureMarker.length;
    final rest = url.substring(restStart);
    final q = rest.indexOf('?');
    final sl = rest.indexOf('/');
    final hash = rest.indexOf('#');
    int cut;
    if (q == -1 && sl == -1 && hash == -1) {
      cut = rest.length;
    } else {
      cut = rest.length;
      if (q != -1 && q < cut) cut = q;
      if (sl != -1 && sl < cut) cut = sl;
      if (hash != -1 && hash < cut) cut = hash;
    }
    final proc = rest.substring(0, cut);
    final tail = rest.substring(cut);
    
    String target;
    // Full procedure name is already correct
    if (proc == 'view' || proc == 'proc') {
      target = proc;
    }
    // Truncated view variants: gw1v, gw1vi, gw1vie, gwa, gwas, gwav, gwavs, gw1v, gw1vi, gw1vie, gwa, gwas, gwav, gwavs
    else if (proc == 'view' || proc == 'v' || proc == 'vi' || proc == 'vie' ||
        proc == 'gwa' || proc == 'gwas' || proc == 'gwav' || proc == 'gwavs' ||
        proc == 'gw1v' || proc == 'gw1vi' || proc == 'gw1vie' ||
        proc == 'gwa' || proc == 'gwas' || proc == 'gwav' || proc == 'gwavs') {
      target = 'view';
    }
    // Truncated proc variants: p, pr, pro, proc, gw1p, gw1pr, gw1pro
    else if (proc == 'proc' || proc == 'p' || proc == 'pr' || proc == 'pro' ||
        proc == 'gw1p' || proc == 'gw1pr' || proc == 'gw1pro') {
      target = 'proc';
    } else {
      return url;
    }
    return url.substring(0, restStart) + target + tail;
  }

  /// Normalize a malformed ITS URL. Idempotent; returns [url] unchanged when
  /// it is not an ITS URL or needs no repair.
  static String normalize(String url) {
    if (url.isEmpty) return url;
    var out = url;
    if (isItsHost(out)) {
      out = out
          .replaceAll('unlven', 'univen')
          .replaceAll('univenerp01', 'univenierp01')
          .replaceAll('univenerip01', 'univenierp01');
      if (out.startsWith('http://')) {
        out = out.replaceFirst('http://', 'https://');
      }
    }
    out = expandProcedure(out);
    return out;
  }
}