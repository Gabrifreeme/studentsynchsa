import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/domain/models/university.dart';
import 'package:studentsyncsa/presentation/providers/university_provider.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

class UniversitiesScreen extends ConsumerStatefulWidget {
  const UniversitiesScreen({super.key});

  @override
  ConsumerState<UniversitiesScreen> createState() => _UniversitiesScreenState();
}

class _UniversitiesScreenState extends ConsumerState<UniversitiesScreen>
    with SingleTickerProviderStateMixin {
  final _searchCtrl = TextEditingController();
  String _selectedProvince = 'All';
  late AnimationController _floatCtrl;
  late Animation<double> _floatAnim;

  static const _provinces = [
    'All', 'Eastern Cape', 'Free State', 'Gauteng',
    'KwaZulu-Natal', 'Limpopo', 'Mpumalanga',
    'Northern Cape', 'North West', 'Western Cape',
  ];

  static const _logoColors = [
    Color(0xFFFFA500), Color(0xFFFFA500), Color(0xFF00FF88),
    Color(0xFFFFA500), Color(0xFFFF4444), Color(0xFF8FD3FF),
    Color(0xFF00FF88), Color(0xFFFFA500),
  ];

  Widget _universitiesStar() {
    return AnimatedBuilder(
      animation: _floatAnim,
      builder: (context, child) => Transform.translate(
        offset: Offset(0, _floatAnim.value),
        child: child,
      ),
      child: GestureDetector(
        onTap: () {
          final message =
              'Search for a university by name, or just scroll down to find '
              'the one you are looking for. Remember, I am here if you want '
              'to ask a question.';
          context.push(
              '/ai-recommendations?message=${Uri.encodeComponent(message)}');
        },
        child: const StarAvatar(size: 40, pulse: true),
      ),
    );
  }

  @override
  void initState() {
    super.initState();
    _floatCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);
    _floatAnim = Tween<double>(begin: -6, end: 6).animate(
      CurvedAnimation(parent: _floatCtrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _floatCtrl.dispose();
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final universitiesAsync = ref.watch(universitiesProvider);

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: Center(
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: double.infinity,
            ),
            child: SafeArea(
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
                    padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        GestureDetector(
                          onTap: () => context.pop(),
                          child: const StarIcon(Icons.arrow_back_rounded, size: 22),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Universities',
                                  style: TextStyle(
                                      color: AppColors.textPrimary,
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold)),
                              const SizedBox(height: 3),
                              Text(
                                'All ${universities.length} SA public universities',
                                style: const TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 10),
                              ),
                            ],
                          ),
                        ),
                        _universitiesStar(),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 7),
                    child: TextField(
                      controller: _searchCtrl,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(color: AppColors.textPrimary, fontSize: 10),
                      decoration: InputDecoration(
                        hintText: 'Search universities...',
                        hintStyle: const TextStyle(color: AppColors.textMuted),
                        prefixIcon: const StarIcon(Icons.search_rounded, size: 22),
                        suffixIcon: IconButton(
                          icon: const StarIcon(Icons.tune_rounded, size: 20),
                          onPressed: () {},
                        ),
                        filled: true,
                        fillColor: AppColors.card,
                        contentPadding: const EdgeInsets.symmetric(vertical: 12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                  ),
                  SizedBox(
                    height: 32,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: _provinces.length,
                      itemBuilder: (_, i) {
                        final p = _provinces[i];
                        final selected = p == _selectedProvince;
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: FilterChip(
                            label: Text(p, style: TextStyle(fontSize: 9, color: selected ? Colors.white : AppColors.textSecondary)),
                            selected: selected,
                            selectedColor: AppColors.primary,
                            backgroundColor: AppColors.surfaceLight,
                            checkmarkColor: AppColors.background,
                            side: BorderSide.none,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                            onSelected: (_) => setState(() => _selectedProvince = p),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 6),
                  Expanded(
                    child: filtered.isEmpty
                        ? const Center(child: Text('No universities found', style: TextStyle(color: AppColors.textMuted)))
                        : GridView.builder(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 2,
                              mainAxisExtent: 118,
                              crossAxisSpacing: 8,
                              mainAxisSpacing: 8,
                            ),
                            itemCount: filtered.length,
                            itemBuilder: (_, i) {
                              return _UniversityCard(
                                university: filtered[i],
                                logoColor: _logoColors[i % _logoColors.length],
                                onTap: () => context.push('/universities/${filtered[i].id}'),
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
        ),
      ),
    );
  }
}

class _UniversityCard extends StatelessWidget {
  final University university;
  final Color logoColor;
  final VoidCallback onTap;

  const _UniversityCard({
    required this.university,
    required this.logoColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final uni = university;
    return AppCard(
      padding: const EdgeInsets.all(AppSpaces.sm + 2),
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(AppSpaces.radius),
              color: logoColor.withValues(alpha: 0.12),
              image: uni.logoUrl.isNotEmpty
                  ? DecorationImage(
                      image: uni.logoUrl.startsWith('assets/')
                          ? AssetImage(uni.logoUrl) as ImageProvider
                          : NetworkImage(uni.logoUrl),
                      fit: BoxFit.contain)
                  : null,
            ),
            child: uni.logoUrl.isEmpty
                ? StarIcon(Icons.account_balance_outlined, size: 18)
                : null,
          ),
          const SizedBox(height: AppSpaces.xs + 2),
          Text(uni.shortName,
              style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 9,
                  fontWeight: FontWeight.w800),
              textAlign: TextAlign.center),
          const SizedBox(height: 2),
          Text(uni.name,
              style: const TextStyle(
                  color: AppColors.textSecondary, fontSize: 9),
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis),
          const Spacer(),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const StarIcon(Icons.location_on_outlined, size: 10),
              const SizedBox(width: 2),
              Flexible(
                child: Text(uni.province,
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 8),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
              ),
            ],
          ),
        ],
      ),
    );
  }

}
