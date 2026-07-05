import 'dart:math';
import 'dart:ui' show lerpDouble;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:go_router/go_router.dart';
import 'package:audioplayers/audioplayers.dart';

enum LassoPhase { idle, winding, swinging, throwing, caught, pulling }

class FakeDownloadScreen extends StatefulWidget {
  const FakeDownloadScreen({super.key});

  @override
  State<FakeDownloadScreen> createState() => _FakeDownloadScreenState();
}

class _FakeDownloadScreenState extends State<FakeDownloadScreen>
    with TickerProviderStateMixin {
  late AnimationController _shakeCtrl;
  late Animation<double> _shakeAnim;
  late AnimationController _starMoveCtrl;
  late AnimationController _starFlipCtrl;
  late AnimationController _dialogEnterCtrl;
  late AnimationController _lassoAnimCtrl;
  final AudioPlayer _audioPlayer = AudioPlayer();

  double _progress = 0.0;
  bool _showStar = false;
  bool _showDialog = false;
  bool _isPulling = false;
  bool _isComplete = false;
  bool _paused = false;
  bool _audioLoaded = false;
  bool _started = false;
  bool _showFinalSpeech = false;
  bool _starFlipped = false;

  String _speechText = '';
  LassoPhase _lassoPhase = LassoPhase.idle;

  Offset _starPos = const Offset(460, 250);

  @override
  void initState() {
    super.initState();
    _shakeCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 100));
    _shakeAnim = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _shakeCtrl, curve: Curves.easeInOut),
    );

    _starMoveCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1000));
    _starFlipCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 400));
    _dialogEnterCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _lassoAnimCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 2500));
  }

  Future<void> _initAudio() async {
    try {
      final data = await rootBundle.load('assets/images/Pull.png');
      final bytes = data.buffer.asUint8List();
      final dataUri = Uri.dataFromBytes(bytes, mimeType: 'audio/mpeg');
      await _audioPlayer.setSource(UrlSource(dataUri.toString()));
      await _audioPlayer.setVolume(0.7);
      _audioLoaded = true;
    } catch (_) {
      _audioLoaded = false;
    }
  }

  Future<void> _playCrunch() async {
    if (!_audioLoaded) return;
    try {
      await _audioPlayer.seek(Duration.zero);
      await _audioPlayer.resume();
    } catch (_) {}
  }

  void _onStart() async {
    if (_started) return;
    setState(() => _started = true);
    await _initAudio();
    _startSequence();
  }

  void togglePause() {
    setState(() => _paused = !_paused);
  }

  Future<void> _wait(int ms) async {
    final steps = ms ~/ 50;
    for (int i = 0; i < steps; i++) {
      while (_paused) {
        if (!mounted) return;
        await Future.delayed(const Duration(milliseconds: 50));
      }
      if (!mounted) return;
      setState(() {});
      await Future.delayed(const Duration(milliseconds: 50));
    }
  }

  Future<void> _moveStarTo(Offset target, {int durationMs = 1000}) async {
    _starMoveCtrl.duration = Duration(milliseconds: durationMs);
    _starMoveCtrl.reset();
    final start = _starPos;
    _starMoveCtrl.addListener(() {
      final t = Curves.easeOutBack.transform(_starMoveCtrl.value);
      setState(() => _starPos = Offset(
        lerpDouble(start.dx, target.dx, t)!,
        lerpDouble(start.dy, target.dy, t)!,
      ));
    });
    await _starMoveCtrl.forward();
  }

  Future<void> _startSequence() async {
    await _wait(800);
    if (!mounted) return;
    setState(() => _showDialog = true);
    _dialogEnterCtrl.forward();

    for (int i = 0; i <= 12; i++) {
      _progress = i / 100.0;
      setState(() {});
      await _wait(120);
    }

    setState(() => _showStar = true);
    await _moveStarTo(const Offset(440, 170), durationMs: 600);
    await _wait(600);

    setState(() => _speechText = "Come on this way!");
    await _wait(2200);
    setState(() => _speechText = "");

    _playCrunch();
    setState(() => _progress = 0.38);
    await _wait(500);

    setState(() => _speechText = "Go that way!");
    await _wait(2200);
    setState(() => _speechText = "");

    setState(() => _progress = 0.45);
    await _wait(500);

    setState(() => _speechText = "Fine, I'll do it myself!");
    await _wait(1500);
    setState(() => _speechText = "");

    setState(() => _lassoPhase = LassoPhase.winding);
    await _wait(700);
    setState(() => _lassoPhase = LassoPhase.swinging);
    _lassoAnimCtrl.repeat();
    await _wait(2500);
    _lassoAnimCtrl.stop();

    setState(() => _lassoPhase = LassoPhase.throwing);
    await _wait(500);

    setState(() => _lassoPhase = LassoPhase.caught);
    await _wait(300);

    setState(() {
      _lassoPhase = LassoPhase.pulling;
      _isPulling = true;
    });
    _shakeCtrl.repeat(reverse: true);

    final startP = 0.45;
    final endP = 1.0;
    for (int i = 0; i <= 20; i++) {
      final t = i / 20.0;
      _progress = startP + (endP - startP) * pow(t, 1.5);
      setState(() {});
      if (i % 4 == 0) _playCrunch();
      await _wait(140);
    }

    _shakeCtrl.stop();
    setState(() {
      _isPulling = false;
      _isComplete = true;
      _lassoPhase = LassoPhase.idle;
      _progress = 1.0;
    });
    await _wait(1000);

    await _moveStarTo(const Offset(240, 170), durationMs: 1000);

    _starFlipCtrl.forward();
    await _wait(400);
    setState(() => _starFlipped = true);

    setState(() => _showFinalSpeech = true);
    await _wait(3000);

    if (mounted) context.go('/dashboard');
  }

  @override
  void dispose() {
    _shakeCtrl.dispose();
    _starMoveCtrl.dispose();
    _starFlipCtrl.dispose();
    _dialogEnterCtrl.dispose();
    _lassoAnimCtrl.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      body: Stack(
        children: [
          Center(child: _buildScene()),
          if (_started)
            Positioned(
              top: 40,
              right: 20,
              child: _buildPauseButton(),
            ),
          if (!_started) _buildStartOverlay(),
        ],
      ),
    );
  }

  Widget _buildStartOverlay() {
    return Positioned.fill(
      child: GestureDetector(
        onTap: _onStart,
        child: Container(
          color: Colors.black54,
          child: Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
              decoration: BoxDecoration(
                color: const Color(0xFF7C3AED),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF7C3AED).withValues(alpha: 0.4),
                    blurRadius: 20,
                  ),
                ],
              ),
              child: const Text(
                'Tap to Download StudentSyncSA',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPauseButton() {
    return GestureDetector(
      onTap: togglePause,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1F2E).withValues(alpha: 0.9),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF2A2F3E)),
        ),
        child: Icon(
          _paused ? Icons.play_arrow_rounded : Icons.pause_rounded,
          color: Colors.white,
          size: 28,
        ),
      ),
    );
  }

  Widget _buildScene() {
    return SizedBox(
      width: 600,
      height: 400,
      child: AnimatedBuilder(
        animation: _shakeAnim,
        builder: (context, _) {
          final shakeOffset = _isPulling
              ? sin(_shakeAnim.value * 6 * pi) * 3.0
              : 0.0;
          return Transform.translate(
            offset: Offset(shakeOffset, 0),
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Positioned(left: 40, top: 10, child: _buildDialog()),
                if (_showStar) _buildStar(),
                if (_lassoPhase != LassoPhase.idle) _buildLasso(),
                if (_showFinalSpeech) _buildFinalSpeech(),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDialog() {
    return AnimatedOpacity(
      opacity: _showDialog ? 1 : 0,
      duration: const Duration(milliseconds: 500),
      child: AnimatedScale(
        scale: _showDialog ? 1 : 0.8,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeOutBack,
        child: SizedBox(
          width: 420,
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF1A1F2E),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFF2A2F3E), width: 1.5),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.6),
                  blurRadius: 40,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: const BoxDecoration(
                    color: Color(0xFF2A3040),
                    borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
                  ),
                  child: Row(
                    children: [
                      Container(width: 12, height: 12,
                          decoration: const BoxDecoration(color: Color(0xFFFF5F57), shape: BoxShape.circle)),
                      const SizedBox(width: 8),
                      Container(width: 12, height: 12,
                          decoration: const BoxDecoration(color: Color(0xFFFEBC2E), shape: BoxShape.circle)),
                      const SizedBox(width: 8),
                      Container(width: 12, height: 12,
                          decoration: const BoxDecoration(color: Color(0xFF28C840), shape: BoxShape.circle)),
                      const SizedBox(width: 16),
                      const Text('sssa.4me',
                          style: TextStyle(color: Color(0xFF888899), fontSize: 13, fontWeight: FontWeight.w500)),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.fromLTRB(28, 24, 28, 32),
                  child: Column(
                    children: [
                      Container(
                        width: 64, height: 64,
                        decoration: BoxDecoration(
                          color: const Color(0xFF7C3AED).withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: const Icon(Icons.download_rounded, color: Color(0xFF7C3AED), size: 32),
                      ),
                      const SizedBox(height: 24),
                      Column(
                        children: [
                          Text(
                            _isComplete ? 'Download complete!' : 'Downloading StudentSyncSA...',
                            style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w700),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _isComplete ? 'Ready to launch' : '${(_progress * 100).round()}% complete',
                            style: TextStyle(
                              color: _isComplete ? const Color(0xFF10B981) : const Color(0xFF888899),
                              fontSize: 14, fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          height: 32,
                          decoration: BoxDecoration(
                            color: const Color(0xFF0A0E17),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: const Color(0xFF2A2F3E)),
                          ),
                          child: FractionallySizedBox(
                            widthFactor: _progress,
                            alignment: Alignment.centerLeft,
                            child: Container(
                              decoration: const BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [Color(0xFF3B82F6), Color(0xFF7C3AED)],
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                      if (_speechText.isNotEmpty && !_isComplete) ...[
                        const SizedBox(height: 20),
                        TweenAnimationBuilder<double>(
                          tween: Tween(begin: 0, end: 1),
                          duration: const Duration(milliseconds: 300),
                          builder: (context, v, _) => Opacity(
                            opacity: v,
                            child: Transform.scale(
                              scale: 0.9 + v * 0.1,
                              child: Container(
                                constraints: const BoxConstraints(maxWidth: 260),
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF2A2F3E),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: const Color(0xFF3B3F4E)),
                                ),
                                child: Text(_speechText,
                                    style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
                              ),
                            ),
                          ),
                        ),
                      ],
                      if (_isComplete) ...[
                        const SizedBox(height: 20),
                        TweenAnimationBuilder<double>(
                          tween: Tween(begin: 0, end: 1),
                          duration: const Duration(milliseconds: 400),
                          builder: (context, v, _) => Opacity(
                            opacity: v,
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.check_circle, color: const Color(0xFF10B981), size: 20 + v * 4),
                                const SizedBox(width: 8),
                                Text('StudentSyncSA downloaded!',
                                    style: TextStyle(color: const Color(0xFF10B981), fontSize: 16, fontWeight: FontWeight.w700)),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStar() {
    return Positioned(
      left: _starPos.dx - 40,
      top: _starPos.dy - 45,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: 1),
        duration: const Duration(milliseconds: 500),
        curve: Curves.easeOutBack,
        builder: (context, v, _) => Opacity(
          opacity: v.clamp(0.0, 1.0),
          child: Transform(
            alignment: Alignment.center,
            transform: Matrix4.identity()
              ..setEntry(0, 0, _starFlipped ? -1.0 : 1.0)
              ..rotateZ(_isPulling ? sin(_shakeAnim.value * 6 * pi) * 0.05 : 0),
            child: SizedBox(
              width: 80,
              height: 90,
              child: Image.asset(
                'assets/images/star_avatar.png',
                fit: BoxFit.contain,
                filterQuality: FilterQuality.high,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLasso() {
    final starPos = Offset(_starPos.dx + 35, _starPos.dy + 30);
    final barLeadingX = 68.0 + _progress * 364.0;
    final targetPos = Offset(barLeadingX, 195);

    return Positioned.fill(
      child: AnimatedBuilder(
        animation: Listenable.merge([_shakeAnim, _lassoAnimCtrl]),
        builder: (context, _) => CustomPaint(
          painter: LassoRenderer(
            phase: _lassoPhase,
            starPos: starPos,
            targetPos: targetPos,
            shakeOffset: _isPulling ? sin(_shakeAnim.value * 6 * pi) * 3.0 : 0,
          ),
        ),
      ),
    );
  }

  Widget _buildFinalSpeech() {
    return Positioned(
      left: _starPos.dx - 80,
      top: _starPos.dy - 75,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: 1),
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeOutBack,
        builder: (context, v, _) => Opacity(
          opacity: v.clamp(0.0, 1.0),
          child: Transform.scale(
            scale: v,
            child: Container(
              constraints: const BoxConstraints(maxWidth: 192),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF2A2F3E),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF3B3F4E)),
              ),
              child: const Text(
                "Hi I'm Star, see you inside!",
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ─── LASSO RENDERER ─────────────────────────────────────────
class LassoRenderer extends CustomPainter {
  final LassoPhase phase;
  final Offset starPos;
  final Offset targetPos;
  final double shakeOffset;
  final double swingValue;

  LassoRenderer({
    required this.phase,
    required this.starPos,
    required this.targetPos,
    this.shakeOffset = 0,
    this.swingValue = 0,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFFD2B48C)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    final sx = starPos.dx;
    final sy = starPos.dy;
    final tx = targetPos.dx + shakeOffset;
    final ty = targetPos.dy;

    switch (phase) {
      case LassoPhase.winding:
        final coilPaint = Paint()
          ..color = const Color(0xFFD2B48C)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..strokeCap = StrokeCap.round;
        for (int i = 0; i < 3; i++) {
          canvas.drawCircle(
            Offset(sx + cos(i * 2.1) * 5, sy + sin(i * 2.1) * 4 - 8),
            3.0 + i,
            coilPaint,
          );
        }
        break;

      case LassoPhase.swinging:
        final angle = swingValue * 4 * pi;
        final radius = 25.0;
        final endX = sx + cos(angle) * radius;
        final endY = sy + sin(angle) * radius;

        final ropePath = Path()
          ..moveTo(sx, sy)
          ..cubicTo(
            sx + cos(angle - 0.5) * radius * 0.5,
            sy + sin(angle - 0.5) * radius * 0.5,
            sx + cos(angle - 0.2) * radius * 0.8,
            sy + sin(angle - 0.2) * radius * 0.8,
            endX, endY,
          );
        canvas.drawPath(ropePath, paint);
        canvas.drawCircle(Offset(endX, endY), 8, paint);
        break;

      case LassoPhase.throwing:
        final midX = (sx + tx) / 2;
        final midY = min(sy, ty) - 50;
        final path = Path()
          ..moveTo(sx, sy)
          ..quadraticBezierTo(midX, midY, tx, ty);
        canvas.drawPath(path, paint);
        break;

      case LassoPhase.caught:
      case LassoPhase.pulling:
        final path = Path()
          ..moveTo(sx, sy)
          ..lineTo(tx, ty);
        canvas.drawPath(path, paint);
        canvas.drawCircle(Offset(tx, ty), 8, paint);
        break;

      case LassoPhase.idle:
        break;
    }
  }

  @override
  bool shouldRepaint(covariant LassoRenderer old) {
    return old.phase != phase ||
        old.starPos != starPos ||
        old.targetPos != targetPos ||
        old.shakeOffset != shakeOffset;
  }
}
