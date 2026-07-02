import 'package:html/parser.dart' as html_parser;
import 'package:html/dom.dart' as dom;

/// Represents a single form field scraped from a university portal page.
class FormField {
  final String name;
  final String type; // 'text' | 'email' | 'tel' | 'select' | 'radio' | 'checkbox' | 'textarea' | 'hidden'
  final String? label;
  final String? placeholder;
  final String currentValue;
  final int maxLength;
  final List<String> options; // for select / radio / checkbox groups
  final bool required;
  final int order; // visual position on the page

  const FormField({
    required this.name,
    required this.type,
    this.label,
    this.placeholder,
    this.currentValue = '',
    this.maxLength = 0,
    this.options = const [],
    this.required = false,
    this.order = 0,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'type': type,
        'label': label,
        'placeholder': placeholder,
        'currentValue': currentValue,
        'maxLength': maxLength,
        'options': options,
        'required': required,
        'order': order,
      };
}

/// Represents a complete HTML form with all its fields.
class ParsedForm {
  final String action;
  final String method;
  final String? encoding;
  final String? name;
  final List<FormField> fields;

  const ParsedForm({
    this.action = '',
    this.method = 'POST',
    this.encoding,
    this.name,
    this.fields = const [],
  });

  /// All fields that are not hidden (editable by the user).
  List<FormField> get fillableFields =>
      fields.where((f) => f.type != 'hidden').toList();

  /// Only the hidden fields (tokens, session keys, etc.).
  List<FormField> get hiddenFields =>
      fields.where((f) => f.type == 'hidden').toList();

  /// Convenience: build a name→value map for all fields.
  Map<String, String> toFieldMap() => {
        for (final f in fields)
          if (f.name.isNotEmpty) f.name: f.currentValue,
      };

  /// Convenience: merge [profileValues] into the field map, respecting maxlength.
  Map<String, String> mergeValues(Map<String, String> profileValues) {
    final result = toFieldMap();
    for (final f in fields) {
      if (f.type == 'hidden') continue;
      final profileValue = profileValues[f.name];
      if (profileValue != null && profileValue.isNotEmpty) {
        result[f.name] = f.maxLength > 0 && profileValue.length > f.maxLength
            ? profileValue.substring(0, f.maxLength)
            : profileValue;
      }
    }
    return result;
  }

  @override
  String toString() =>
      'ParsedForm(action: $action, ${fillableFields.length} fillable, '
      '${hiddenFields.length} hidden)';
}

/// Scrapes and parses the first <form> containing oap* fields from [html].
///
/// If no oap* form is found, falls back to the first <form> on the page.
ParsedForm parsePortalForm(String html) {
  final doc = html_parser.parse(html);

  // Try to find the application form (the one with oap* / P_* fields)
  dom.Element? targetForm;
  for (final form in doc.querySelectorAll('form')) {
    final inner = form.innerHtml.toLowerCase();
    if (inner.contains('oap') || inner.contains('p_')) {
      targetForm = form;
      break;
    }
  }
  targetForm ??= doc.querySelector('form');

  if (targetForm == null) {
    return const ParsedForm();
  }

  final action = _resolveAction(targetForm, doc);
  final method =
      (targetForm.attributes['method'] ?? 'POST').toUpperCase();
  final encoding = targetForm.attributes['enctype'];
  final formName = targetForm.attributes['name'];
  final fields = <FormField>[];
  int order = 0;

  // ── Extract all input, select, textarea elements ──────────────────────────

  final allElements = targetForm.querySelectorAll(
      'input, select, textarea');

  for (final el in allElements) {
    final tag = el.localName;
    if (tag == 'input') {
      final type = (el.attributes['type'] ?? 'text').toLowerCase();
      final name = el.attributes['name'] ?? '';
      if (name.isEmpty) continue;

      if (type == 'submit' || type == 'button' || type == 'reset' ||
          type == 'image') {
        continue;
      }

      final value = el.attributes['value'] ?? '';
      final label = _resolveLabel(el, allElements, doc);
      final placeholder = el.attributes['placeholder'];
      final maxLen = int.tryParse(el.attributes['maxlength'] ?? '') ?? 0;
      final required = el.attributes.containsKey('required');

      if (type == 'radio' || type == 'checkbox') {
        // Group radios/checkboxes by name — only add once
        final existingIdx =
            fields.indexWhere((f) => f.name == name && f.type == type);
        if (existingIdx == -1) {
          final options = <String>[];
          for (final same in allElements) {
            if (same.localName == 'input' &&
                (same.attributes['type'] ?? '').toLowerCase() == type &&
                same.attributes['name'] == name) {
              final v = same.attributes['value'] ?? '';
              if (!options.contains(v)) options.add(v);
            }
          }
          fields.add(FormField(
            name: name,
            type: type,
            label: label,
            currentValue: value,
            options: options,
            required: required,
            order: order++,
          ));
        }
      } else {
        fields.add(FormField(
          name: name,
          type: type,
          label: label,
          placeholder: placeholder,
          currentValue: value,
          maxLength: maxLen,
          required: required,
          order: order++,
        ));
      }
    } else if (tag == 'select') {
      final name = el.attributes['name'] ?? '';
      if (name.isEmpty) continue;

      final label = _resolveLabel(el, allElements, doc);
      final required = el.attributes.containsKey('required');
      final options = <String>[];
      String selectedValue = '';
      int maxLen = 0;

      for (final opt in el.querySelectorAll('option')) {
        final v = opt.attributes['value'] ?? opt.text.trim();
        options.add(v);
        if (v.length > maxLen) maxLen = v.length;
        if (opt.attributes.containsKey('selected')) {
          selectedValue = v;
        }
      }

      fields.add(FormField(
        name: name,
        type: 'select',
        label: label,
        currentValue: selectedValue,
        options: options,
        maxLength: maxLen,
        required: required,
        order: order++,
      ));
    } else if (tag == 'textarea') {
      final name = el.attributes['name'] ?? '';
      if (name.isEmpty) continue;

      fields.add(FormField(
        name: name,
        type: 'textarea',
        label: _resolveLabel(el, allElements, doc),
        placeholder: el.attributes['placeholder'],
        currentValue: el.text.trim(),
        maxLength: int.tryParse(el.attributes['maxlength'] ?? '') ?? 0,
        required: el.attributes.containsKey('required'),
        order: order++,
      ));
    }
  }

  // Sort by visual order
  fields.sort((a, b) => a.order.compareTo(b.order));

  return ParsedForm(
    action: action,
    method: method,
    encoding: encoding,
    name: formName,
    fields: fields,
  );
}

// ── Helpers ────────────────────────────────────────────────────────────────────

/// Resolves the form's action to an absolute URL.
String _resolveAction(dom.Element form, dom.Document doc) {
  var action = form.attributes['action'] ?? '';
  if (action.isEmpty) return '';

  final base = doc.querySelector('base')?.attributes['href'];
  final uri = Uri.tryParse(action);
  if (uri != null && uri.hasScheme) return action;

  // Relative URL — resolve against <base> or document URL
  if (base != null) {
    final baseUri = Uri.tryParse(base);
    if (baseUri != null) return baseUri.resolveUri(uri!).toString();
  }

  return action;
}

/// Tries to find a human-readable label for [el] by checking:
/// 1. aria-label attribute
/// 2. <label for="id"> matching the element's id
/// 3. Parent <label> that wraps the element
/// 4. Preceding text node in the same parent
String _resolveLabel(dom.Element el, List<dom.Element> all, dom.Document doc) {
  // aria-label
  final aria = el.attributes['aria-label'];
  if (aria != null && aria.trim().isNotEmpty) return aria.trim();

  // aria-labelledby
  final labelledBy = el.attributes['aria-labelledby'];
  if (labelledBy != null) {
    for (final id in labelledBy.split(' ')) {
      final ref = doc.getElementById(id);
      if (ref != null) {
        final text = ref.text.trim();
        if (text.isNotEmpty) return text;
      }
    }
  }

  // <label for="...">
  final id = el.attributes['id'];
  if (id != null) {
    for (final label in all) {
      if (label.localName == 'label' && label.attributes['for'] == id) {
        final text = label.text.trim();
        if (text.isNotEmpty) return text;
      }
    }
  }

  // Parent <label> that wraps the element
  var parent = el.parent;
  while (parent != null) {
    if (parent.localName == 'label') {
      final text = parent.text.trim();
      if (text.isNotEmpty) return text;
      break;
    }
    parent = parent.parent;
  }

  // Preceding text node sibling
  final siblings = el.parent?.nodes ?? [];
  final idx = siblings.indexOf(el);
  for (int i = idx - 1; i >= 0; i--) {
    final sib = siblings[i];
    if (sib is dom.Text) {
      final text = sib.text.trim();
      if (text.isNotEmpty) return text;
    }
  }

  return '';
}
