import 'package:flutter/material.dart';
import 'package:studentsyncsa/core/theme/app_theme.dart';

/// Single spacing / typography scale shared by every screen.
/// Sizes are tuned mobile-first; desktop simply gets the same values.
class AppSpaces {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;

  static const double radius = 12;
  static const double tileIcon = 18;
  static const double tileTitle = 13;
  static const double tileSubtitle = 10;
  static const double tileChevron = 14;
}

class GradientBackground extends StatelessWidget {
  final Widget child;
  const GradientBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color(0xFF000000),
            Color(0xFF0A0A0A),
            Color(0xFF000000),
          ],
        ),
      ),
      child: child,
    );
  }
}

class StarAvatar extends StatelessWidget {
  final double size;
  final bool pulse;

  const StarAvatar({super.key, this.size = 48, this.pulse = false});

  @override
  Widget build(BuildContext context) {
    Widget image = ClipOval(
      child: Image.asset(
        'assets/images/star_avatar.png',
        width: size,
        height: size,
        fit: BoxFit.cover,
        filterQuality: FilterQuality.high,
      ),
    );
    if (pulse) {
      image = _PulseWrapper(child: image);
    }
    return image;
  }
}

class _PulseWrapper extends StatefulWidget {
  final Widget child;
  const _PulseWrapper({required this.child});

  @override
  State<_PulseWrapper> createState() => _PulseWrapperState();
}

class _PulseWrapperState extends State<_PulseWrapper>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
    _anim = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (context, child) {
        return Transform.scale(
          scale: _anim.value,
          child: child,
        );
      },
      child: widget.child,
    );
  }
}

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final VoidCallback? onTap;

  const AppCard({super.key, required this.child, this.padding, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppSpaces.radius),
        child: Padding(
          padding: padding ?? const EdgeInsets.all(AppSpaces.lg),
          child: child,
        ),
      ),
    );
  }
}

class SectionHeader extends StatelessWidget {
  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;

  const SectionHeader({
    super.key,
    required this.title,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 1.5,
          ),
        ),
        if (actionLabel != null)
          GestureDetector(
            onTap: onAction,
            child: Text(
              actionLabel!,
              style: const TextStyle(
                color: AppColors.primaryLight,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
      ],
    );
  }
}

class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle = '',
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: AppColors.textMuted),
            const SizedBox(height: 16),
            Text(
              title,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
              textAlign: TextAlign.center,
            ),
            if (subtitle.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                subtitle,
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class SyncStatusBadge extends StatelessWidget {
  final String status;
  const SyncStatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    IconData icon;
    switch (status) {
      case 'syncing':
        color = AppColors.info;
        icon = Icons.sync_rounded;
        break;
      case 'synced':
        color = AppColors.success;
        icon = Icons.cloud_done_rounded;
        break;
      case 'failed':
        color = AppColors.error;
        icon = Icons.cloud_off_rounded;
        break;
      default:
        color = AppColors.textMuted;
        icon = Icons.cloud_off_rounded;
    }
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 4),
        Text(
          status == 'syncing' ? 'Syncing...' : status[0].toUpperCase() + status.substring(1),
          style: TextStyle(color: color, fontSize: 11),
        ),
      ],
    );
  }
}


/// Standard tappable row used across the dashboard, lists and settings.
class AppListTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final VoidCallback? onTap;
  final Color? iconColor;
  final Widget? trailing;
  final bool compact;

  const AppListTile({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
    this.onTap,
    this.iconColor,
    this.trailing,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    if (compact) {
      return AppCard(
        padding: const EdgeInsets.symmetric(
            horizontal: AppSpaces.sm, vertical: AppSpaces.md),
        onTap: onTap,
        child: SizedBox(
          height: 52,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Icon(icon,
                  color: iconColor ?? AppColors.primaryLight,
                  size: AppSpaces.tileIcon),
              const SizedBox(height: AppSpaces.xs),
              Text(label,
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: AppSpaces.tileTitle,
                      fontWeight: FontWeight.w800)),
            ],
          ),
        ),
      );
    }
    return AppCard(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpaces.md, vertical: AppSpaces.sm + 2),
      onTap: onTap,
      child: Row(
        children: [
          StarIcon(icon, size: AppSpaces.tileIcon),
          const SizedBox(width: AppSpaces.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: AppSpaces.tileTitle,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.3)),
                if (value.isNotEmpty) ...[
                  const SizedBox(height: AppSpaces.xs),
                  Text(value,
                      style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: AppSpaces.tileSubtitle)),
                ],
              ],
            ),
          ),
          trailing ?? const Icon(Icons.chevron_right_rounded,
              color: AppColors.textMuted, size: AppSpaces.tileChevron),
        ],
      ),
    );
  }
}


/// Icon painted with the South African Star palette. Use this for every icon
/// so the UI keeps the same multicolour language as the Star / Google icons.
class StarIcon extends StatelessWidget {
  final IconData icon;
  final double size;

  const StarIcon(this.icon, {super.key, this.size = 18});

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      shaderCallback: (bounds) => const LinearGradient(
        colors: [
          AppColors.starRed,
          AppColors.starBlue,
          AppColors.starGreen,
          AppColors.starYellow,
        ],
        stops: [0.0, 0.34, 0.67, 1.0],
      ).createShader(bounds),
      blendMode: BlendMode.srcIn,
      child: Icon(icon, size: size, color: Colors.white),
    );
  }
}
