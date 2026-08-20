import 'package:flutter/material.dart';
import '../models/postal_code.dart';
import 'postal_code_picker.dart';

/// A [FormField] that lets the user pick a [PostalCode] via
/// [showPostalCodePicker] and reports the result through the standard form
/// APIs ([validator], [onSaved], [onChanged], [enabled]).
///
/// `isRequired` adds a default "Please select a postal code" validator when
/// no explicit [validator] is supplied. (Parameter is named `isRequired`
/// rather than `required` because `required` is a reserved Dart keyword.)
class PostalCodeFormField extends FormField<PostalCode> {
  PostalCodeFormField({
    super.key,
    super.initialValue,
    bool isRequired = false,
    List<PostalCode> recentCodes = const [],
    FormFieldValidator<PostalCode>? validator,
    super.onSaved,
    ValueChanged<PostalCode?>? onChanged,
    super.enabled,
    bool readOnly = false,
    InputDecoration? decoration,
    String? hintText,
  }) : super(
          validator: validator ??
              (isRequired
                  ? (PostalCode? v) => v == null || v.isEmpty
                      ? 'Please select a postal code'
                      : null
                  : null),
          builder: (FormFieldState<PostalCode> state) => _PostalCodeFormFieldContent(
            value: state.value,
            enabled: enabled,
            readOnly: readOnly,
            decoration:
                (decoration ?? InputDecoration()).copyWith(hintText: hintText),
            recentCodes: recentCodes,
            onPicked: (PostalCode? v) {
              state.didChange(v);
              onChanged?.call(v);
            },
          ),
        );

}

class _PostalCodeFormFieldContent extends StatefulWidget {
  const _PostalCodeFormFieldContent({
    required this.value,
    required this.enabled,
    required this.readOnly,
    required this.decoration,
    required this.recentCodes,
    required this.onPicked,
  });

  final PostalCode? value;
  final bool enabled;
  final bool readOnly;
  final InputDecoration decoration;
  final List<PostalCode> recentCodes;
  final ValueChanged<PostalCode?> onPicked;

  @override
  State<_PostalCodeFormFieldContent> createState() =>
      _PostalCodeFormFieldContentState();
}

class _PostalCodeFormFieldContentState
    extends State<_PostalCodeFormFieldContent> {
  @override
  Widget build(BuildContext context) {
    final canOpen = widget.enabled && !widget.readOnly;
    final theme = Theme.of(context);
    final text = widget.value?.description ?? '';
    final hasValue = widget.value != null;
    final effectiveDecoration = widget.decoration
        .applyDefaults(theme.inputDecorationTheme)
        .copyWith(
          prefixIcon: widget.readOnly
              ? null
              : const Icon(Icons.location_on_outlined),
          suffixIcon: hasValue && widget.enabled
              ? IconButton(
                  icon: const Icon(Icons.clear, size: 18),
                  tooltip: 'Clear',
                  visualDensity: VisualDensity.compact,
                  onPressed: () => widget.onPicked(null),
                )
              : null,
        );

    return InkWell(
      onTap: canOpen ? _openPicker : null,
      child: InputDecorator(
        decoration: effectiveDecoration,
        child: Row(
          children: [
            Expanded(
              child: Text(
                text.isEmpty
                    ? (widget.decoration.hintText ?? 'Select a postal code')
                    : text,
                style: TextStyle(
                  color: text.isEmpty
                      ? theme.hintColor
                      : theme.textTheme.bodyLarge?.color,
                ),
              ),
            ),
            if (!widget.readOnly) const Icon(Icons.arrow_drop_down),
          ],
        ),
      ),
    );
  }

  void _openPicker() {
    final ctx = context;
    if (!ctx.mounted) return;
    FocusScope.of(ctx).unfocus();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final picked = await showPostalCodePicker(
        context: ctx,
        recents: widget.recentCodes,
      );
      if (mounted) {
        widget.onPicked(picked);
      }
    });
  }
}
