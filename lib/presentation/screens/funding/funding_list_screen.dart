import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/data/datasources/mock_bursary_data.dart';
import 'package:studentsynchsa/domain/models/bursary.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';

class FundingListScreen extends StatefulWidget {
  const FundingListScreen({super.key});

  @override
  State<FundingListScreen> createState() => _FundingListScreenState();
}

class _FundingListScreenState extends State<FundingListScreen> {
  final _searchCtrl = TextEditingController();
  String _selectedType = 'All';
  final Set<String> _saved = {};

  static const _filterTypes = ['All', 'Bursary', 'Scholarship', 'Nsfas', 'Loan', 'Grant'];

  static const _typeColors = {
    'Bursary': Color(0xFF7C3AED),
    'Scholarship': Color(0xFF3B82F6),
    'Nsfas': Color(0xFF10B981),
    'Loan': Color(0xFFF59E0B),
    'Grant': Color(0xFFEF4444),
  };

  static const _logoColors = [
    Color(0xFF7C3AED), Color(0xFF3B82F6), Color(0xFF10B981),
    Color(0xFFF59E0B), Color(0xFFEF4444), Color(0xFFEC4899),
  ];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bursaries = MockBursaryData.all;

    var filtered = bursaries.where((b) {
      if (_selectedType != 'All' && b.type != _selectedType) return false;
      if (_searchCtrl.text.isNotEmpty) {
        final q = _searchCtrl.text.toLowerCase();
        if (!b.name.toLowerCase().contains(q) &&
            !b.provider.toLowerCase().contains(q)) {
          return false;
        }
      }
      return true;
    }).toList();

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Funding & Bursaries',
                        style: TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 26,
                            fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text('${bursaries.length} programmes available',
                        style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 14)),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                child: TextField(
                  controller: _searchCtrl,
                  onChanged: (_) => setState(() {}),
                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: 'Search programmes...',
                    hintStyle: const TextStyle(color: AppColors.textMuted),
                    prefixIcon: const Icon(Icons.search_rounded, color: AppColors.textMuted, size: 22),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.tune_rounded, color: AppColors.textMuted, size: 20),
                      onPressed: () {},
                    ),
                    filled: true,
                    fillColor: AppColors.card,
                    contentPadding: const EdgeInsets.symmetric(vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
              ),
              SizedBox(
                height: 40,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  itemCount: _filterTypes.length,
                  itemBuilder: (_, i) {
                    final t = _filterTypes[i];
                    final selected = t == _selectedType;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: FilterChip(
                        label: Text(t,
                            style: TextStyle(
                                fontSize: 12,
                                color: selected
                                    ? Colors.white
                                    : AppColors.textSecondary)),
                        selected: selected,
                        selectedColor: AppColors.primary,
                        backgroundColor: AppColors.surfaceLight,
                        checkmarkColor: Colors.white,
                        side: BorderSide.none,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20)),
                        onSelected: (_) => setState(() => _selectedType = t),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 8),
              Expanded(
                child: filtered.isEmpty
                    ? const Center(
                        child: Text('No programmes found',
                            style: TextStyle(color: AppColors.textMuted)))
                    : ListView.builder(
                        padding:
                            const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                        itemCount: filtered.length,
                        itemBuilder: (_, i) {
                          final b = filtered[i];
                          return _FundingCard(
                            bursary: b,
                            logoColor: _logoColors[i % _logoColors.length],
                            typeColor:
                                _typeColors[b.type] ?? AppColors.primary,
                            isSaved: _saved.contains(b.id),
                            onTap: () => context.push('/funding/${b.id}'),
                            onSave: () {
                              setState(() {
                                if (_saved.contains(b.id)) {
                                  _saved.remove(b.id);
                                } else {
                                  _saved.add(b.id);
                                }
                              });
                            },
                            onOpenLink: () {},
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FundingCard extends StatelessWidget {
  final Bursary bursary;
  final Color logoColor;
  final Color typeColor;
  final bool isSaved;
  final VoidCallback onTap;
  final VoidCallback onSave;
  final VoidCallback onOpenLink;

  const _FundingCard({
    required this.bursary,
    required this.logoColor,
    required this.typeColor,
    required this.isSaved,
    required this.onTap,
    required this.onSave,
    required this.onOpenLink,
  });

  @override
  Widget build(BuildContext context) {
    final b = bursary;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        color: AppColors.card,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: logoColor.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(Icons.school_outlined, color: logoColor, size: 24),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            b.name,
                            style: const TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            b.provider,
                            style: const TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.open_in_new,
                          size: 18, color: AppColors.textMuted),
                      onPressed: onOpenLink,
                      splashRadius: 20,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                    const SizedBox(width: 12),
                    IconButton(
                      icon: Icon(
                        isSaved ? Icons.bookmark : Icons.bookmark_border,
                        size: 20,
                        color: isSaved ? AppColors.primaryLight : AppColors.textMuted,
                      ),
                      onPressed: onSave,
                      splashRadius: 20,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: typeColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    b.type,
                    style: TextStyle(
                      color: typeColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  b.coverage.isNotEmpty ? b.coverage : b.description,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 12,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}