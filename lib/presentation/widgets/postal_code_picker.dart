import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/sa_postal_codes.dart';

/// A complete, searchable picker for South African postal codes.
///
/// Features:
///  - Structured dataset parsed into code / suburb / city.
///  - Ranked search by code, suburb or city with match highlighting.
///  - A-Z index rail for browsing the full list.
///  - Recently selected postal codes.
///  - Manual entry fallback for codes not in the dataset.
class PostalCodePicker {
  PostalCodePicker._();

  /// Returns the selected postal code, or null if the user cancels.
  static Future<String?> show(
    BuildContext context, {
    String? initialCode,
  }) {
    return showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => _PostalCodePickerSheet(initialCode: initialCode),
    );
  }
}

/// A single postal code record.
class PostalCodeEntry {
  const PostalCodeEntry({
    required this.code,
    required this.suburb,
    this.city = '',
  });

  final String code;
  final String suburb;
  final String city;
}

/// Parsed, deduplicated and sorted dataset plus session recents.
class PostalCodeData {
  PostalCodeData._();

  static const int recentLimit = 6;

  static final List<PostalCodeEntry> all = _build();
  static final List<String> letters = _collectLetters();
  static final List<PostalCodeEntry> _recent = [];

  static List<PostalCodeEntry> get recent => List.unmodifiable(_recent);
  static bool get hasRecent => _recent.isNotEmpty;

  static List<PostalCodeEntry> _build() {
    final seen = <String>{};
    final out = <PostalCodeEntry>[];
    for (final raw in saPostalCodes) {
      final dash = raw.indexOf(' - ');
      if (dash <= 0) continue;

      final code = raw.substring(0, dash).trim();
      if (code.length != 4) continue; // skip country / LOV entries

      var rest = raw.substring(dash + 3).trim();
      var suburb = rest;
      var city = '';
      final comma = rest.indexOf(',');
      if (comma >= 0) {
        suburb = rest.substring(0, comma).trim();
        city = rest.substring(comma + 1).trim();
      }
      if (suburb.isEmpty) continue;

      final key = '$code|${suburb.toLowerCase()}';
      if (!seen.add(key)) continue;

      out.add(PostalCodeEntry(code: code, suburb: suburb, city: city));
    }

    out.sort((a, b) {
      final s = a.suburb.toLowerCase().compareTo(b.suburb.toLowerCase());
      if (s != 0) return s;
      final c = a.city.toLowerCase().compareTo(b.city.toLowerCase());
      if (c != 0) return c;
      return a.code.compareTo(b.code);
    });
    return out;
  }

  static List<String> _collectLetters() {
    final set = <String>{};
    for (final e in all) {
      set.add(letterOf(e.suburb));
    }
    return set.toList()..sort();
  }

  /// First A-Z character of [value], or '#' when it starts with a digit/symbol.
  static String letterOf(String value) {
    for (final codeUnit in value.toUpperCase().codeUnits) {
      if (codeUnit >= 0x41 && codeUnit <= 0x5A) {
        return String.fromCharCode(codeUnit);
      }
    }
    return '#';
  }

  static void addRecent(PostalCodeEntry entry) {
    _recent.removeWhere((e) => e.code == entry.code && e.suburb == entry.suburb);
    _recent.insert(0, entry);
    if (_recent.length > recentLimit) {
      _recent.removeRange(recentLimit, _recent.length);
    }
  }

  static void removeRecent(PostalCodeEntry entry) {
    _recent.removeWhere((e) => e.code == entry.code && e.suburb == entry.suburb);
  }
}

class _PostalCodePickerSheet extends StatefulWidget {
  const _PostalCodePickerSheet({this.initialCode});

  final String? initialCode;

  @override
  State<_PostalCodePickerSheet> createState() => _PostalCodePickerSheetState();
}

class _BrowseRow {
  const _BrowseRow.header(this.letter) : isHeader = true, entry = null;
  const _BrowseRow.item(this.entry) : isHeader = false, letter = null;

  final bool isHeader;
  final String? letter;
  final PostalCodeEntry? entry;
}

class _Match {
  const _Match(this.entry, this.score);

  final PostalCodeEntry entry;
  final int score;
}

class _PostalCodePickerSheetState extends State<_PostalCodePickerSheet> {
  static const double _headerH = 34;
  static const double _itemH = 66;
  static const int _maxResults = 200;

  final _searchCtrl = TextEditingController();
  final _searchFocus = FocusNode();
  final _scrollCtrl = ScrollController();

  late final List<_BrowseRow> _browseRows;
  late final Map<String, double> _letterOffsets;
  String? _selectedLetter;

  @override
  void initState() {
    super.initState();
    final initial = widget.initialCode?.trim();
    if (initial != null && initial.isNotEmpty) {
      _searchCtrl.text = initial;
    }
    _buildBrowseRows();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _searchFocus.requestFocus();
    });
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    _searchFocus.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _buildBrowseRows() {
    final rows = <_BrowseRow>[];
    final offsets = <String, double>{};
    var offset = 0.0;
    String? current;
    for (final e in PostalCodeData.all) {
      final letter = PostalCodeData.letterOf(e.suburb);
      if (letter != current) {
        current = letter;
        rows.add(_BrowseRow.header(letter));
        offsets[letter] = offset;
        offset += _headerH;
      }
      rows.add(_BrowseRow.item(e));
      offset += _itemH;
    }
    _browseRows = rows;
    _letterOffsets = offsets;
  }

  List<PostalCodeEntry> _search(String rawQuery) {
    final q = rawQuery.trim().toLowerCase();
    if (q.isEmpty) return const [];

    final matches = <_Match>[];
    final seen = <String>{};
    for (final e in PostalCodeData.all) {
      final code = e.code.toLowerCase();
      final suburb = e.suburb.toLowerCase();
      final city = e.city.toLowerCase();

      int score;
      if (code == q) {
        score = 0;
      } else if (code.startsWith(q)) {
        score = 1;
      } else if (suburb.startsWith(q)) {
        score = 2;
      } else if (city.isNotEmpty && city.startsWith(q)) {
        score = 3;
      } else if (code.contains(q)) {
        score = 4;
      } else if (suburb.contains(q)) {
        score = 5;
      } else if (city.isNotEmpty && city.contains(q)) {
        score = 6;
      } else {
        continue;
      }

      final key = '${e.code}|$suburb';
      if (!seen.add(key)) continue;
      matches.add(_Match(e, score));
    }

    matches.sort((a, b) {
      if (a.score != b.score) return a.score.compareTo(b.score);
      final s = a.entry.suburb
          .toLowerCase()
          .compareTo(b.entry.suburb.toLowerCase());
      if (s != 0) return s;
      return a.entry.code.compareTo(b.entry.code);
    });

    return matches.map((m) => m.entry).toList();
  }

  void _select(PostalCodeEntry e) {
    PostalCodeData.addRecent(e);
    Navigator.pop(context, e.code);
  }

  void _jumpToLetter(String letter) {
    final offset = _letterOffsets[letter];
    if (offset == null) return;
    HapticFeedback.selectionClick();
    setState(() => _selectedLetter = letter);

    if (_scrollCtrl.hasClients) {
      _scrollCtrl.jumpTo(offset.clamp(0.0, _scrollCtrl.position.maxScrollExtent));
    } else {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && _scrollCtrl.hasClients) {
          _scrollCtrl.jumpTo(
            offset.clamp(0.0, _scrollCtrl.position.maxScrollExtent),
          );
        }
      });
    }
  }

  void _handleIndexDrag(double dy, double height) {
    final letters = PostalCodeData.letters;
    final cell = height / letters.length;
    final idx = (dy / cell).floor().clamp(0, letters.length - 1);
    _jumpToLetter(letters[idx]);
  }

  List<InlineSpan> _highlight(String text, String q) {
    if (q.isEmpty) return [TextSpan(text: text)];
    final lower = text.toLowerCase();
    final spans = <InlineSpan>[];
    var start = 0;
    while (start < text.length) {
      final idx = lower.indexOf(q, start);
      if (idx < 0) {
        spans.add(TextSpan(text: text.substring(start)));
        break;
      }
      if (idx > start) {
        spans.add(TextSpan(text: text.substring(start, idx)));
      }
      spans.add(TextSpan(
        text: text.substring(idx, idx + q.length),
        style: const TextStyle(
          color: AppColors.primaryLight,
          fontWeight: FontWeight.w700,
        ),
      ));
      start = idx + q.length;
    }
    return spans;
  }

  @override
  Widget build(BuildContext context) {
    final query = _searchCtrl.text;
    final q = query.trim().toLowerCase();
    final results = _search(query);
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    final sheetHeight = MediaQuery.of(context).size.height * 0.78;

    return Padding(
      padding: EdgeInsets.only(bottom: bottomInset),
      child: SizedBox(
        height: sheetHeight,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 8),
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(4, 8, 4, 0),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.close),
                    tooltip: 'Cancel',
                    onPressed: () => Navigator.pop(context),
                  ),
                  const Expanded(
                    child: Text(
                      'Select Postal Code',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 48),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
              child: TextField(
                controller: _searchCtrl,
                focusNode: _searchFocus,
                textInputAction: TextInputAction.search,
                decoration: InputDecoration(
                  hintText: 'Search by code, suburb or city...',
                  prefixIcon: const Icon(
                    Icons.search,
                    color: AppColors.textMuted,
                  ),
                  suffixIcon: query.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 18),
                          onPressed: () {
                            _searchCtrl.clear();
                            setState(() {});
                          },
                        )
                      : null,
                ),
                onChanged: (v) {
                  setState(() {});
                  if (v.trim().isEmpty &&
                      _scrollCtrl.hasClients &&
                      _scrollCtrl.offset != 0) {
                    _scrollCtrl.jumpTo(0);
                  }
                },
              ),
            ),
            if (q.isEmpty) _buildRecents(),
            _buildStatus(query, results),
            const Divider(height: 1),
            Expanded(child: _buildList(query, results)),
          ],
        ),
      ),
    );
  }

  Widget _buildRecents() {
    final recents = PostalCodeData.recent;
    if (recents.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(left: 16, right: 16, bottom: 6),
      child: Row(
        children: [
          const Text(
            'RECENT',
            style: TextStyle(
              fontSize: 11,
              letterSpacing: 1.2,
              fontWeight: FontWeight.w600,
              color: AppColors.textMuted,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: SizedBox(
              height: 30,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: recents.length,
                separatorBuilder: (_, _) => const SizedBox(width: 6),
                itemBuilder: (_, i) {
                  final e = recents[i];
                  return _RecentChip(
                    entry: e,
                    onTap: () => _select(e),
                    onRemove: () =>
                        setState(() => PostalCodeData.removeRecent(e)),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatus(String query, List<PostalCodeEntry> results) {
    String text;
    if (query.trim().isEmpty) {
      text = '${PostalCodeData.all.length.toString()} suburbs across '
          'South Africa';
    } else if (results.isEmpty) {
      text = 'No matches';
    } else if (results.length > _maxResults) {
      text = 'Showing first $_maxResults of ${results.length} matches';
    } else {
      text = results.length == 1
          ? '1 match'
          : '${results.length} matches';
    }
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
      child: Text(
        text,
        style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
      ),
    );
  }

  Widget _buildList(String query, List<PostalCodeEntry> results) {
    if (query.trim().isEmpty) {
      return Stack(
        children: [
          ListView.builder(
            controller: _scrollCtrl,
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            padding: const EdgeInsets.only(right: 26, bottom: 12),
            itemCount: _browseRows.length,
            itemBuilder: (_, i) => _buildBrowseRow(_browseRows[i]),
          ),
          _buildIndexRail(),
        ],
      );
    }
    if (results.isEmpty) {
      return _buildNoResults(query);
    }
    return ListView.builder(
      controller: _scrollCtrl,
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      padding: const EdgeInsets.only(bottom: 12),
      itemCount: results.length > _maxResults ? _maxResults : results.length,
      itemBuilder: (_, i) => _buildItem(results[i], query.trim().toLowerCase()),
    );
  }

  Widget _buildBrowseRow(_BrowseRow row) {
    if (row.isHeader) {
      return Container(
        height: _headerH,
        color: AppColors.surfaceLight.withValues(alpha: 0.5),
        alignment: Alignment.centerLeft,
        padding: const EdgeInsets.only(left: 16),
        child: Text(
          row.letter!,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.2,
            color: AppColors.textMuted,
          ),
        ),
      );
    }
    return _buildItem(row.entry!, '');
  }

  Widget _buildItem(PostalCodeEntry e, String q) {
    return SizedBox(
      height: _itemH,
      child: InkWell(
        onTap: () => _select(e),
        splashColor: AppColors.primary.withValues(alpha: 0.08),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              Container(
                width: 58,
                padding: const EdgeInsets.symmetric(vertical: 6),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: AppColors.primary.withValues(alpha: 0.35),
                  ),
                ),
                child: Text(
                  e.code,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                    color: AppColors.primaryLight,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text.rich(
                      TextSpan(
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                        children: _highlight(e.suburb, q),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (e.city.isNotEmpty)
                      Text.rich(
                        TextSpan(
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                          children: _highlight(e.city, q),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(
                Icons.chevron_right,
                size: 18,
                color: AppColors.textMuted,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIndexRail() {
    final letters = PostalCodeData.letters;
    return Positioned(
      right: 2,
      top: 0,
      bottom: 0,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final cell = constraints.maxHeight / letters.length;
          return GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTapDown: (d) =>
                _handleIndexDrag(d.localPosition.dy, constraints.maxHeight),
            onVerticalDragStart: (d) =>
                _handleIndexDrag(d.localPosition.dy, constraints.maxHeight),
            onVerticalDragUpdate: (d) =>
                _handleIndexDrag(d.localPosition.dy, constraints.maxHeight),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (final letter in letters)
                  SizedBox(
                    height: cell,
                    child: Center(
                      child: AnimatedDefaultTextStyle(
                        duration: const Duration(milliseconds: 120),
                        style: TextStyle(
                          fontSize: letter == _selectedLetter ? 13 : 10,
                          fontWeight: FontWeight.w700,
                          color: letter == _selectedLetter
                              ? AppColors.textPrimary
                              : AppColors.primaryLight,
                        ),
                        child: Text(letter),
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildNoResults(String query) {
    final code = query.trim();
    final isCode = RegExp(r'^\d{4}$').hasMatch(code);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.search_off, size: 40, color: AppColors.textMuted),
          const SizedBox(height: 8),
          const Text(
            'No suburbs match your search',
            style: TextStyle(color: AppColors.textMuted),
          ),
          if (isCode) ...[
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () =>
                  _select(PostalCodeEntry(code: code, suburb: code)),
              icon: const Icon(Icons.pin_drop_outlined, size: 18),
              label: Text('Use postal code $code'),
            ),
          ],
        ],
      ),
    );
  }
}

class _RecentChip extends StatelessWidget {
  const _RecentChip({
    required this.entry,
    required this.onTap,
    required this.onRemove,
  });

  final PostalCodeEntry entry;
  final VoidCallback onTap;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final label = entry.suburb.isEmpty || entry.suburb == entry.code
        ? entry.code
        : '${entry.code} · ${entry.suburb}';
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(15),
      child: Container(
        padding: const EdgeInsets.only(left: 10, right: 4),
        decoration: BoxDecoration(
          color: AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(15),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(width: 4),
            GestureDetector(
              onTap: onRemove,
              child: const Padding(
                padding: EdgeInsets.all(4),
                child: Icon(
                  Icons.close,
                  size: 14,
                  color: AppColors.textMuted,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
