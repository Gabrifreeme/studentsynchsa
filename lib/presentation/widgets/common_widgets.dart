import 'package:flutter/material.dart';
import 'package:lipsyncstudent/core/theme/app_theme.dart';

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
            Color(0xFF0D2158),
            Color(0xFF0F1624),
            Color(0xFF181818),
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
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _anim = Tween<double>(begin: 0.6, end: 1.15).animate(
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
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: padding ?? const EdgeInsets.all(16),
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


class AcesiDropdown<T> extends StatelessWidget {
  final T? initialValue;
  final String? labelText;
  final IconData? prefixIcon;
  final InputDecoration? decoration;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?>? onChanged;
  final String? Function(T?)? validator;
  final bool isExpanded;
  final Widget? icon;
  final Color? dropdownColor;
  final TextStyle? style;
  final BorderRadius? borderRadius;

  const AcesiDropdown({
    super.key,
    this.initialValue,
    this.labelText,
    this.prefixIcon,
    this.decoration,
    required this.items,
    this.onChanged,
    this.validator,
    this.isExpanded = true,
    this.icon,
    this.dropdownColor,
    this.style,
    this.borderRadius,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveDecoration = decoration ??
        InputDecoration(
          labelText: labelText,
          labelStyle: const TextStyle(color: AppColors.textMuted),
          prefixIcon: prefixIcon != null
              ? Icon(prefixIcon, color: AppColors.primary)
              : null,
          border: const OutlineInputBorder(
            borderRadius: BorderRadius.zero,
            borderSide: BorderSide(color: AppColors.primary, width: 1),
          ),
          enabledBorder: const OutlineInputBorder(
            borderRadius: BorderRadius.zero,
            borderSide: BorderSide(color: AppColors.primary, width: 1),
          ),
          focusedBorder: const OutlineInputBorder(
            borderRadius: BorderRadius.zero,
            borderSide: BorderSide(color: AppColors.primary, width: 2),
          ),
        );

    return DropdownButtonFormField<T>(
      initialValue: initialValue,
      isExpanded: isExpanded,
      dropdownColor: dropdownColor ?? Colors.black,
      iconEnabledColor: AppColors.primary,
      icon: icon ?? const Icon(Icons.keyboard_arrow_down, color: AppColors.primary),
      borderRadius: borderRadius ?? BorderRadius.zero,
      style: style ??
          const TextStyle(color: AppColors.primary, fontSize: 14, fontFamily: 'monospace'),
      decoration: effectiveDecoration,
      items: items.map((item) {
        return DropdownMenuItem<T>(
          value: item.value,
          child: _AcesiHoverItem(child: item.child),
        );
      }).toList(),
      onChanged: onChanged,
      validator: validator,
    );
  }
}

class _AcesiHoverItem extends StatefulWidget {
  final Widget child;
  const _AcesiHoverItem({required this.child});

  @override
  State<_AcesiHoverItem> createState() => _AcesiHoverItemState();
}

class _AcesiHoverItemState extends State<_AcesiHoverItem> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      cursor: SystemMouseCursors.click,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 80),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        color: _hovering
            ? AppColors.primary.withValues(alpha: 0.25)
            : Colors.transparent,
        child: DefaultTextStyle.merge(
          style: const TextStyle(color: AppColors.primary, fontSize: 14),
          child: widget.child,
        ),
      ),
    );
  }
}


