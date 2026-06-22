import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/providers/university_provider.dart';
import 'package:studentsyncsa/presentation/screens/universities/offline_tab.dart';
import 'package:studentsyncsa/presentation/screens/universities/university_webview_screen.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';


const Map<String, List<String>> _uniImages = {
  'cput': ['assets/images/Cape.png', 'assets/images/Cape1.png'],
  'dut': ['assets/images/Durban.png', 'assets/images/Durban1.png'],
  'mandela': ['assets/images/Nelson.png', 'assets/images/Nelson1.png'],
  'nwu': ['assets/images/Nwu.png', 'assets/images/Nwu1.png'],
  'ru': ['assets/images/Rhodes.png', 'assets/images/Rhodes1.png'],
  'spu': ['assets/images/Sol.png', 'assets/images/Sol1.png'],
  'su': ['assets/images/Stellen.png', 'assets/images/Stellen1.png'],
  'tut': ['assets/images/Tsh.png', 'assets/images/Tsh1.png'],
  'uchenn': ['assets/images/Uct.png', 'assets/images/Uct1.png'],
  'ufh': ['assets/images/Fort.png', 'assets/images/Fort1.png'],
  'uj': ['assets/images/Uj.png', 'assets/images/Uj1.png'],
  'ukzn': ['assets/images/Kwa.png', 'assets/images/Kwa1.png'],
  'ul': ['assets/images/Lim.png', 'assets/images/Lim1.png'],
  'unisa': ['assets/images/Uni.png', 'assets/images/Uni1.png'],
  'ufs': ['assets/images/Free.png', 'assets/images/Free1.png'],
  'wsu': ['assets/images/Walter.png', 'assets/images/Walter1.png'],
  'wits': ['assets/images/Wits.png', 'assets/images/Wits1.png'],
  'zululand': ['assets/images/Zulu.png', 'assets/images/Zulu1.png'],
  'mru': ['assets/images/Man.png', 'assets/images/Man1.png'],
  'cut': ['assets/images/Cuo.png', 'assets/images/Cuo1.png'],
  'univen': ['assets/images/Ven.png', 'assets/images/Ven1.png'],
  'vut': ['assets/images/Vaal.png', 'assets/images/Vaal1.png'],
};

class UniversityDetailScreen extends ConsumerWidget {
  final String universityId;
  const UniversityDetailScreen({super.key, required this.universityId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final universityAsync = ref.watch(universitiesProvider);
    final uni = universityAsync.valueOrNull?.where((u) => u.id == universityId).firstOrNull;

    if (uni == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('University Details')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(title: Text(uni.shortName)),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Apply button (top)
              _SparkleStar(
                onTap: () => _launchUrl(context, uni.applicationUrl),
              ),
              const SizedBox(height: 16),

              // Fee + NBT info
              _infoChip(Icons.monetization_on_outlined,
                'Application Fee: R ${uni.hasApplicationFee ? uni.applicationFee?.toStringAsFixed(0) ?? '' : '0'}'),
              const SizedBox(height: 8),
              _infoChip(Icons.assignment_outlined,
                'NBT: ${uni.requiresNbt ? "Required" : "Not Required"}'),
              const SizedBox(height: 16),

              // Offline Resources
              AppCard(
                child: Column(
                  children: [
                    OfflineTab(universityId: uni.id),
                    if (_uniImages.containsKey(uni.id)) ...[
                      const SizedBox(height: 12),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.asset(_uniImages[uni.id]![0],
                            width: double.infinity, fit: BoxFit.cover),
                      ),
                      const SizedBox(height: 8),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.asset(_uniImages[uni.id]![1],
                            width: double.infinity, fit: BoxFit.cover),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Header (logo + name, location, description below)
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.asset(
                            'assets/images/${uni.id}_logo.png',
                            width: 48, height: 48, fit: BoxFit.contain,
                            errorBuilder: (_, _, _) => const SizedBox(width: 48),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(uni.name,
                              style: const TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.textPrimary)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.location_on_outlined,
                            size: 16, color: AppColors.textSecondary),
                        const SizedBox(width: 4),
                        Text(uni.province,
                            style: const TextStyle(color: AppColors.textSecondary)),
                      ],
                    ),
                    if (uni.description.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(uni.description,
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 13)),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _infoChip(IconData icon, String label) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 14),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.15)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.starGold),
          const SizedBox(width: 10),
          Flexible(
            child: Text(label,
                style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary)),
          ),
        ],
      ),
    );
  }

  Future<void> _launchUrl(BuildContext context, String url) async {
    if (url.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No online portal available'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => UniversityWebViewScreen(
          url: url,
          universityName: '',
        ),
      ),
    );
  }
}

class _SparkleStar extends StatefulWidget {
  final VoidCallback onTap;
  const _SparkleStar({required this.onTap});

  @override
  State<_SparkleStar> createState() => _SparkleStarState();
}

class _SparkleStarState extends State<_SparkleStar>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scale;
  late Animation<double> _rotate;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _scale = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _rotate = Tween<double>(begin: 0, end: 0.15).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    _controller.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        _controller.reverse();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.scale(
          scale: _scale.value,
          child: Transform.rotate(
            angle: _rotate.value,
            child: child,
          ),
        );
      },
      child: Material(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            _controller.forward();
            widget.onTap();
          },
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              gradient: const LinearGradient(
                colors: [AppColors.primary, AppColors.primaryDark],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.primary.withValues(alpha: 0.3),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text('✨',
                    style: TextStyle(fontSize: 20)),
                SizedBox(width: 10),
                Text(
                  'Apply Now',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
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
