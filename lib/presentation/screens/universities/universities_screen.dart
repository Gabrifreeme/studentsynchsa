import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsynchsa/core/theme/app_theme.dart';
import 'package:studentsynchsa/domain/models/university.dart';
import 'package:studentsynchsa/presentation/providers/university_provider.dart';
import 'package:studentsynchsa/presentation/widgets/common_widgets.dart';

class UniversitiesScreen extends ConsumerStatefulWidget {
  const UniversitiesScreen({super.key});

  @override
  ConsumerState<UniversitiesScreen> createState() => _UniversitiesScreenState();
}

class _UniversitiesScreenState extends ConsumerState<UniversitiesScreen> {
  final _searchCtrl = TextEditingController();
  String _selectedProvince = 'All';
  final Set<String> _bookmarked = {};

  static const _provinces = [
    'All', 'Eastern Cape', 'Free State', 'Gauteng',
    'KwaZulu-Natal', 'Limpopo', 'Mpumalanga',
    'Northern Cape', 'North West', 'Western Cape',
  ];

  static const _logoColors = [
    Color(0xFF7C3AED), Color(0xFF3B82F6), Color(0xFF10B981),
    Color(0xFFF59E0B), Color(0xFFEF4444), Color(0xFFEC4899),
    Color(0xFF14B8A6), Color(0xFF8B5CF6),
  ];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final universitiesAsync = ref.watch(universitiesProvider);

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: SafeArea(
          child: universitiesAsync.when(
            data: (universities) {
              var filtered = universities.where((u) {
                if (_selectedProvince != 'All' && u.province != _selectedProvince) {
                  return false;
                }
                if (_searchCtrl.text.isNotEmpty) {
                  final q = _searchCtrl.text.toLowerCase();
                  if (!u.name.toLowerCase().contains(q) &&
                      !u.shortName.toLowerCase().contains(q)) {
                    return false;
                  }
                }
                return true;
              }).toList();

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Universities',
                            style: TextStyle(
                                color: AppColors.textPrimary,
                                fontSize: 26,
                                fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text('All ${universities.length} SA public universities',
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
                        hintText: 'Search universities...',
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
                      itemCount: _provinces.length,
                      itemBuilder: (_, i) {
                        final p = _provinces[i];
                        final selected = p == _selectedProvince;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            label: Text(p, style: TextStyle(fontSize: 12, color: selected ? Colors.white : AppColors.textSecondary)),
                            selected: selected,
                            selectedColor: AppColors.primary,
                            backgroundColor: AppColors.surfaceLight,
                            checkmarkColor: Colors.white,
                            side: BorderSide.none,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                            onSelected: (_) => setState(() => _selectedProvince = p),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 8),
                  Expanded(
                    child: filtered.isEmpty
                        ? const Center(child: Text('No universities found', style: TextStyle(color: AppColors.textMuted)))
                        : ListView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                            itemCount: filtered.length,
                            itemBuilder: (_, i) {
                              return _UniversityCard(
                                university: filtered[i],
                                logoColor: _logoColors[i % _logoColors.length],
                                isBookmarked: _bookmarked.contains(filtered[i].id),
                                onTap: () => context.push('/universities/${filtered[i].id}'),
                                onBookmark: () {
                                  setState(() {
                                    if (_bookmarked.contains(filtered[i].id)) {
                                      _bookmarked.remove(filtered[i].id);
                                    } else {
                                      _bookmarked.add(filtered[i].id);
                                    }
                                  });
                                },
                                onOpenLink: () {},
                              );
                            },
                          ),
                  ),
                ],
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => EmptyState(
              icon: Icons.error_outline,
              title: 'Failed to load universities',
              subtitle: e.toString(),
            ),
          ),
        ),
      ),
    );
  }
}

class _UniversityCard extends StatelessWidget {
  final University university;
  final Color logoColor;
  final bool isBookmarked;
  final VoidCallback onTap;
  final VoidCallback onBookmark;
  final VoidCallback onOpenLink;

  const _UniversityCard({
    required this.university,
    required this.logoColor,
    required this.isBookmarked,
    required this.onTap,
    required this.onBookmark,
    required this.onOpenLink,
  });

  @override
  Widget build(BuildContext context) {
    final uni = university;
    final statusTag = _buildStatusTag(uni);

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
                      child: Icon(Icons.account_balance_outlined, color: logoColor, size: 24),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            uni.name,
                            style: const TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            uni.shortName,
                            style: const TextStyle(
                              color: AppColors.primaryLight,
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.open_in_new, size: 18, color: AppColors.textMuted),
                      onPressed: onOpenLink,
                      splashRadius: 20,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                    const SizedBox(width: 12),
                    IconButton(
                      icon: Icon(
                        isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                        size: 20,
                        color: isBookmarked ? AppColors.primaryLight : AppColors.textMuted,
                      ),
                      onPressed: onBookmark,
                      splashRadius: 20,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Icon(Icons.location_on_outlined, size: 14, color: AppColors.textSecondary),
                    const SizedBox(width: 4),
                    Text(
                      uni.province,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                statusTag,
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatusTag(University uni) {
    if (uni.hasApplicationFee && uni.applicationFee != null && uni.applicationFee! > 0) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.attach_money_rounded, size: 14, color: AppColors.primaryLight),
          const SizedBox(width: 3),
          Text(
            'Fee: R${uni.applicationFee!.toInt()}',
            style: const TextStyle(
              color: AppColors.primaryLight,
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      );
    }
    return const Text(
      'No NBT or fee',
      style: TextStyle(
        color: AppColors.success,
        fontSize: 11,
        fontWeight: FontWeight.w500,
      ),
    );
  }
}