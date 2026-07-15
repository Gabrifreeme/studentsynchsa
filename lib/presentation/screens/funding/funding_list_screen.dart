import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/data/datasources/mock_bursary_data.dart';
import 'package:studentsyncsa/domain/models/bursary.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

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
                    prefixIcon: const Icon(Icons.search_rounded, color: AppColors.primaryLight, size: 22),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.tune_rounded, color: AppColors.primaryLight, size: 20),
                      onPressed: () {},
                    ),
                    filled: true,
                    fillColor: AppColors.surface,
                    contentPadding: const EdgeInsets.symmetric(vertical: 12),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide(color: AppColors.border),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide(
                        color: AppColors.border.withValues(alpha: 0.5),
                      ),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: const BorderSide(
                        color: AppColors.primary,
                        width: 1.5,
                      ),
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
                                fontWeight: selected
                                    ? FontWeight.w700
                                    : FontWeight.w500,
                                color: selected
                                    ? Colors.white
                                    : AppColors.textSecondary)),
                        selected: selected,
                        selectedColor: AppColors.primary,
                        backgroundColor: AppColors.surface,
                        checkmarkColor: Colors.white,
                        side: BorderSide(
                          color: selected
                              ? AppColors.primary
                              : AppColors.border.withValues(alpha: 0.5),
                        ),
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

class _FundingCard extends StatefulWidget {
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
  State<_FundingCard> createState() => _FundingCardState();
}

class _FundingCardState extends State<_FundingCard>
    with TickerProviderStateMixin {
  late final AnimationController _pulseCtrl;
  late final AnimationController _spinCtrl;
  late final Animation<double> _pulse;
  late final Animation<double> _spin;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _spinCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _pulse = Tween<double>(begin: 0.6, end: 1.4).animate(
      CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut),
    );
    _spin = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _spinCtrl, curve: Curves.easeOutCubic),
    );
    _pulseCtrl.addListener(() => setState(() {}));
    _spinCtrl.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _spinCtrl.dispose();
    super.dispose();
  }

  void _handleApplyNow(BuildContext context, Bursary b) async {
    final url = b.applicationUrl.isNotEmpty ? b.applicationUrl : b.website;
    if (url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No application link available'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    if (_spinCtrl.isCompleted || _spinCtrl.status == AnimationStatus.dismissed) {
      await _spinCtrl.forward(from: 0.0);
    }
    if (!context.mounted) return;
    final uri = Uri.encodeComponent(b.applicationUrl);
    final name = Uri.encodeComponent(b.name);
    context.push('/funding/${b.id}/webview?url=$uri&name=$name');
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.bursary;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        color: AppColors.surface,
        elevation: 2,
        shadowColor: AppColors.primary.withValues(alpha: 0.15),
        child: InkWell(
          onTap: widget.onTap,
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
                        color: widget.logoColor.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(Icons.school_outlined, color: widget.logoColor, size: 24),
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
                      onPressed: widget.onOpenLink,
                      splashRadius: 20,
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                    const SizedBox(width: 12),
                    IconButton(
                      icon: Icon(
                        widget.isSaved ? Icons.bookmark : Icons.bookmark_border,
                        size: 20,
                        color: widget.isSaved ? AppColors.primaryLight : AppColors.textMuted,
                      ),
                      onPressed: widget.onSave,
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
                    color: widget.typeColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    b.type,
                    style: TextStyle(
                      color: widget.typeColor,
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
                const SizedBox(height: 12),
                // Apply [Star] Now – star pulsates, whole button spins & shrinks on tap
                Opacity(
                  opacity: 1.0 - _spin.value,
                  child: Transform(
                    alignment: Alignment.center,
                    transform: Matrix4.identity()
                      ..rotateZ(_spin.value * 4 * 6.2832),
                    child: Transform.scale(
                      scale: 1.0 - _spin.value,
                      child: InkWell(
                        onTap: () => _handleApplyNow(context, b),
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            vertical: 12,
                            horizontal: 16,
                          ),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                AppColors.primary.withValues(alpha: 0.2),
                                AppColors.primary.withValues(alpha: 0.08),
                              ],
                              begin: Alignment.centerLeft,
                              end: Alignment.centerRight,
                            ),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: AppColors.primary.withValues(alpha: 0.4),
                              width: 1.2,
                            ),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Text(
                                'Apply',
                                style: TextStyle(
                                  color: AppColors.primaryLight,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Transform.scale(
                                scale: _pulse.value,
                                child: Container(
                                  padding: const EdgeInsets.all(2),
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    boxShadow: [
                                      BoxShadow(
                                        color: AppColors.primary
                                            .withValues(alpha: 0.4),
                                        blurRadius: 8,
                                        spreadRadius: 1,
                                      ),
                                    ],
                                  ),
                                  child: Image.asset(
                                    'assets/images/star_avatar.png',
                                    width: 22,
                                    height: 22,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              const Text(
                                'Now',
                                style: TextStyle(
                                  color: AppColors.primaryLight,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
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
