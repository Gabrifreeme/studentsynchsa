import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';
import 'package:studentsyncsa/presentation/providers/university_provider.dart';
import 'package:studentsyncsa/presentation/screens/universities/offline_tab.dart';
import 'package:studentsyncsa/presentation/widgets/common_widgets.dart';

final _random = math.Random();


const _bundledLogoIds = {'smu', 'ump', 'up', 'uwc'};

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
  'smu': ['assets/logos/smu.png', 'assets/logos/smu.png'],
  'ump': ['assets/logos/ump.png', 'assets/logos/ump.png'],
  'up': ['assets/logos/up.png', 'assets/logos/up.png'],
  'uwc': ['assets/logos/uwc.png', 'assets/logos/uwc.png'],
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
        appBar: AppBar(
          leading: IconButton(
            icon: const StarIcon(Icons.arrow_back_rounded, size: 20),
            onPressed: () => Navigator.of(context).pop(),
          ),
          title: const Text('University Details'),
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          automaticallyImplyLeading: false,
          title: Text(uni.shortName),
        ),
        body: Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width < 600
                  ? double.infinity
                  : 620,
            ),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Align(
                    alignment: Alignment.centerLeft,
                    child: GestureDetector(
                      onTap: () => Navigator.of(context).pop(),
                      child: const StarIcon(Icons.arrow_back_rounded, size: 20),
                    ),
                  ),
                  const SizedBox(height: 8),

                  // 1. University identity card
                  AppCard(
                    child: SizedBox(
                      width: double.infinity,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(6),
                                child: Image.asset(
                                  (_bundledLogoIds.contains(uni.id)
                                  ? 'assets/logos/${uni.id}.png'
                                  : 'assets/images/${uni.id}_logo.png'),
                                  width: 40, height: 40, fit: BoxFit.contain,
                                  errorBuilder: (_, _, _) =>
                                      const SizedBox(width: 28),
                                ),
                              ),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(uni.name,
                                    style: const TextStyle(
                                        fontSize: 15,
                                        fontWeight: FontWeight.bold,
                                        color: AppColors.textPrimary)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          GestureDetector(
                            onTap: () async {
                              final query = Uri.encodeComponent(
                                  '${uni.name}, ${uni.province}, South Africa');
                              await launchUrl(
                                Uri.parse(
                                    'https://www.google.com/maps/search/?api=1&query=$query'),
                                mode: LaunchMode.externalApplication,
                              );
                            },
                            child: Row(
                              children: [
                                const StarIcon(Icons.location_on_outlined,
                                    size: 14),
                                const SizedBox(width: 3),
                                Text(uni.province,
                                    style: const TextStyle(
                                        color: AppColors.textSecondary)),
                                const SizedBox(width: 8),
                                Text(
                                  'Tap for directions',
                                  style: TextStyle(
                                      color: AppColors.primaryLight,
                                      fontSize: 10,
                                      decoration: TextDecoration.underline),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),

                  // 2. Offline guide
                  AppCard(
                    child: SizedBox(
                      width: double.infinity,
                      child: OfflineTab(universityId: uni.id),
                    ),
                  ),
                  const SizedBox(height: 6),

                  // Fee + NBT
                  _infoChip(Icons.monetization_on_outlined,
                    'Application Fee: R ${uni.hasApplicationFee ? uni.applicationFee?.toStringAsFixed(0) ?? '' : '0'}'),
                  const SizedBox(height: 6),
                  _infoChip(Icons.assignment_outlined,
                    'NBT: ${uni.requiresNbt ? "Required" : "Not Required"}'),
                  const SizedBox(height: 8),

                  // 3. Image card - same width as every other card
                  if (_uniImages.containsKey(uni.id))
                    AppCard(
                      child: Row(
                        children: [
                          Expanded(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(6),
                              child: Image.asset(_uniImages[uni.id]![0],
                                  width: double.infinity,
                                  height: 120,
                                  fit: BoxFit.cover),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(6),
                              child: Image.asset(_uniImages[uni.id]![1],
                                  width: double.infinity,
                                  height: 120,
                                  fit: BoxFit.cover),
                            ),
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 40),

                  // 4. Apply button centred under the image card
                  OutlinedButton.icon(
                    onPressed: () => _launchUniv(context, uni),
                    icon: const StarIcon(Icons.auto_awesome_rounded, size: 16),
                    label: const Text('Apply'),
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(120, 36),
                      side: const BorderSide(color: AppColors.primary),
                      foregroundColor: AppColors.primary,
                      textStyle: const TextStyle(fontSize: 12),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Opens ${uni.shortName}\'s official application page',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 9),
                  ),
                ],
              ),
            ),
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
        borderRadius: BorderRadius.circular(7),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.15)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AppColors.starGold),
          const SizedBox(width: 7),
          Flexible(
            child: Text(label,
                style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary)),
          ),
        ],
      ),
    );
  }

  Future<void> _launchUniv(BuildContext context, dynamic university) async {
    final url = (university.applicationUrl as String?)?.isNotEmpty == true
        ? university.applicationUrl as String
        : university.website as String;
    try {
      await launchUrl(Uri.parse(url),
          mode: LaunchMode.externalApplication);
    } catch (_) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not open $url')),
      );
    }
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
  late Animation<double> _rotation;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    _rotation = Tween<double>(begin: 0, end: 8 * math.pi).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInCubic),
    );
    _scale = TweenSequence<double>([
      TweenSequenceItem(weight: 0.5, tween: ConstantTween(1.0)),
      TweenSequenceItem(weight: 0.5, tween: Tween(begin: 1.0, end: 0.0)),
    ]).animate(_controller);
    _controller.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        widget.onTap();
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
    return Stack(
      clipBehavior: Clip.none,
      children: [
        AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return Transform.scale(
              scale: _scale.value,
              child: Transform.rotate(
                angle: _rotation.value,
                child: child,
              ),
            );
          },
          child: Material(
            color: AppColors.primary,
            borderRadius: BorderRadius.circular(11),
            child: InkWell(
              borderRadius: BorderRadius.circular(11),
              onTap: () {
                if (!_controller.isAnimating) {
                  _controller.forward(from: 0);
                }
              },
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 16),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(11),
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
                        style: TextStyle(fontSize: 14)),
                    SizedBox(width: 7),
                    Text(
                      'Apply Now',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        AnimatedBuilder(
          animation: _controller,
          builder: (context, _) {
            return CustomPaint(
              painter: _FirecrackerPainter(progress: _controller.value),
              size: Size.zero,
            );
          },
        ),
      ],
    );
  }
}

class _FirecrackerPainter extends CustomPainter {
  final double progress;
  static List<_Particle>? _particles;

  _FirecrackerPainter({required this.progress}) {
    if (_particles == null) {
      _generate();
    }
  }

  static void _generate() {
    _particles = List.generate(45, (i) {
      final angle = _random.nextDouble() * 2 * math.pi;
      final speed = 60.0 + _random.nextDouble() * 120.0;
      final colors = [
        AppColors.primary,
        AppColors.primaryLight,
        AppColors.info,
        AppColors.success,
        AppColors.primaryDark,
        Colors.white,
      ];
      return _Particle(
        angle: angle,
        speed: speed,
        color: colors[i % colors.length],
        size: 2.5 + _random.nextDouble() * 4.5,
        delay: _random.nextDouble() * 0.25,
      );
    });
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (progress <= 0 || progress >= 1) return;

    final center = Offset(size.width / 2, size.height / 2);
    final particles = _particles;
    if (particles == null) return;

    for (final p in particles) {
      final local = (progress - p.delay).clamp(0.0, 1.0);
      if (local <= 0) continue;

      final dist = p.speed * local;
      final x = center.dx + math.cos(p.angle) * dist;
      final y = center.dy + math.sin(p.angle) * dist;
      final opacity = (1.0 - local).clamp(0.0, 1.0);
      final pSize = p.size * (1.0 - local * 0.4);

      canvas.drawCircle(
        Offset(x, y),
        pSize,
        Paint()..color = p.color.withValues(alpha: opacity),
      );
    }
  }

  @override
  bool shouldRepaint(_FirecrackerPainter old) => old.progress != progress;
}

class _Particle {
  final double angle;
  final double speed;
  final Color color;
  final double size;
  final double delay;
  const _Particle({
    required this.angle,
    required this.speed,
    required this.color,
    required this.size,
    required this.delay,
  });
}
