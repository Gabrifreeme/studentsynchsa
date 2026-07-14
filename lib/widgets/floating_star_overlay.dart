import 'package:flutter/material.dart';

class FloatingStarOverlay {
  static OverlayEntry? _entry;

  static void show(BuildContext context, ValueNotifier<String> currentUrl) {
    hide();
    _entry = OverlayEntry(
      builder: (context) => Positioned(
        bottom: 16,
        right: 16,
        child: _SparkleStarOverlay(currentUrl: currentUrl),
      ),
    );
    Overlay.of(context).insert(_entry!);
  }

  static void hide() {
    _entry?.remove();
    _entry = null;
  }
}

class _SparkleStarOverlay extends StatefulWidget {
  final ValueNotifier<String> currentUrl;
  const _SparkleStarOverlay({required this.currentUrl});

  @override
  State<_SparkleStarOverlay> createState() => _SparkleStarOverlayState();
}

class _SparkleStarOverlayState extends State<_SparkleStarOverlay> {
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: Text('Star Guide'),
            content: Text('Guide message here'),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: Text('OK'),
              ),
            ],
          ),
        );
      },
      child: Image.asset('assets/images/star_avatar.png', width: 40, height: 40),
    );
  }
}
