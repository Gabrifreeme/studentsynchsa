import '../data/sa_postal_codes.dart';
import '../models/postal_code.dart';

/// Loads and caches the South African postal-code dataset used by the ITS
/// portal picker. Sourced from the ITS OAP LOV in `sa_postal_codes.dart`.
class PostalCodeRepository {
  PostalCodeRepository._();

  static List<PostalCode>? _cache;

  /// Loads (and caches) the full postal-code list.
  static List<PostalCode> load() => _load();

  /// Async variant used by `showPostalCodePicker`; returns the cached list.
  static Future<List<PostalCode>> ensureLoaded() async => _load();

  /// Full-text search over code / description / region.
  static List<PostalCode> search(String query) {
    final q = query.toLowerCase().trim();
    if (q.isEmpty) return _load();
    return _load()
        .where((p) =>
            p.code.toLowerCase().contains(q) ||
            p.description.toLowerCase().contains(q) ||
            (p.region != null && p.region!.toLowerCase().contains(q)))
        .toList();
  }

  static List<PostalCode> _load() {
    if (_cache != null) return _cache!;
    final out = <PostalCode>[];
    for (final raw in saPostalCodes) {
      final parsed = PostalCode.parse(raw);
      // Keep only 4-digit codes (skips country / LOV entries like "117 - ANGOLA").
      if (parsed.code.length != 4) continue;
      out.add(parsed);
    }
    out.sort((a, b) {
      final c = a.code.compareTo(b.code);
      return c != 0 ? c : a.description.compareTo(b.description);
    });
    _cache = out;
    return out;
  }
}
